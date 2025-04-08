#!/usr/bin/env cs_python

import argparse
import json
import numpy as np

from cerebras.sdk.runtime.sdkruntimepybind import SdkRuntime, MemcpyDataType # pylint: disable=no-name-in-module
from cerebras.sdk.runtime.sdkruntimepybind import MemcpyOrder # pylint: disable=no-name-in-module

import matplotlib.pyplot as plt


def get_A(m, n):
    matrix = np.arange(m * n).reshape(m, n)

    # Reverse the order of odd-indexed rows (1, 3, 5, ...)
    for i in range(1, m, 2):
        matrix[i] = matrix[i, ::-1]

    return matrix

def permute_random(matrix):
    flat_matrix = matrix.flatten()
    np.random.shuffle(flat_matrix)
    return flat_matrix.reshape(matrix.shape)

def permute_v(matrix):
    return np.fliplr(matrix)

def permute_h(matrix):
    return np.flipud(matrix)

def set_bottomright(matrix):
    m = matrix.copy()
    m[-1, -1] = 0
    return m

def make_u48(words):
    return words[0] + (words[1] << 16) + (words[2] << 32)

def convert_tsc(matrix):
    T = np.zeros((matrix.shape[0], matrix.shape[1])).astype(int)
    word = np.zeros(3).astype(np.uint16)
    for col in range(matrix.shape[0]):
        for row in range(matrix.shape[1]):
            word[0] = matrix[(col, row, 0)]
            word[1] = matrix[(col, row, 1)]
            word[2] = matrix[(col, row, 2)]
            T[col, row] = make_u48(word)
    return T

    

parser = argparse.ArgumentParser()
parser.add_argument('--name', help='the test name')
parser.add_argument('--iters', default=200, help='the test name')
parser.add_argument('--seed', default=1337, help='test random seed')
parser.add_argument('--threads', default=8, help='number of threads')
parser.add_argument('--img', default=False, action='store_true', help='download an image for every iteration')
args = parser.parse_args()
if args.img:
	import matplotlib.pyplot as plt
	import os
dirname = args.name
np.random.seed(seed=int(args.seed))


# Parse the compile metadata
with open(f"{dirname}/out.json", encoding="utf-8") as json_file:
  compile_data = json.load(json_file)
params = compile_data["params"]
Px = int(params["Px"])
Py = int(params["Py"])
dx = int(params["dx"])
dy = int(params["dy"])

print(f"Px := width of the core = {Px}")
print(f"Py := height of the core = {Py}")
print(f"dx := width per core = {dx}")
print(f"dy := height per core = {dy}")

assert(dx >= 4)
assert(dy >= 4)
assert(dy % 2 == 0)
assert(dx % 2 == 0)

Nx = Px * dx
Ny = Py * dy

print(f"Nx = {Nx}, Ny = {Ny}")

memcpy_dtype = MemcpyDataType.MEMCPY_32BIT
runner = SdkRuntime(dirname, cmaddr=None, suppress_simfab_trace=True, msg_level="INFO", simfab_numthreads=args.threads)

sym_data = runner.get_id("data")
sym_tsc_t0 = runner.get_id("tsc_t0")
sym_tsc_t1 = runner.get_id("tsc_t1")

runner.load()
runner.run()

print("Generate test Matrix")
A_sorted = get_A(Ny, Nx).astype(np.int32)
A = permute_random(A_sorted)
#A = set_bottomright(A_sorted)
#A_sorted[0, 0] = 0
print("A_sorted = ", A_sorted)
print("A = ", A)

print("step 1: copy mode H2D(data)")
data = np.stack(np.split(np.stack(np.split(A, Px, axis=1)), Py, axis=1)).ravel()
runner.memcpy_h2d(sym_data, data, 0, 0, Px, Py, dx * dy, \
    streaming=False, data_type=memcpy_dtype, order=MemcpyOrder.ROW_MAJOR, nonblock=True)

print("step 3: call f_init for one time initialization")
runner.launch("f_init", nonblock=False)

# TODO HW 1.2: Implement your own on-wafer convergence check
slow_convergence_check_to_be_optimized_by_you = True

total_time = 0

A_last = np.zeros(Nx * Ny, np.int32)
if args.img:
	os.makedirs("img", exist_ok=True)
	plt.imshow(A_last, cmap='viridis', interpolation='nearest')
	# Add a colorbar
	plt.colorbar()
	# Save the figure to a file
	plt.savefig(f"img/iter_{i}.png", dpi=300, bbox_inches='tight')
	# Close the figure to free memory
	plt.close()


for i in range(int(args.iters)):
	print("================ Host Iter: ", i, " ================")
	print("step 4: call f_run_y to test scatter and gather")
	runner.launch("f_step", nonblock=False)

	print("step 5: sync")
	runner.launch("f_sync", nonblock=False)

	print("copy mode D2H(data) to test convergence")
	A_next = np.zeros(Nx * Ny, np.int32)
	runner.memcpy_d2h(A_next, sym_data, 0, 0, Px, Py, dx * dy, \
	    streaming=False, data_type=memcpy_dtype, order=MemcpyOrder.ROW_MAJOR, nonblock=False)
	A_next = A_next.reshape(Py, Px, dy, dx).swapaxes(1, 2).reshape(Ny, Nx)
	if np.array_equal(A_last, A_next):
		break
	A_last = A_next

	print("step 6: get start times")
	tsc_t0 = np.zeros(Px*Py*3, np.uint32)
	print(tsc_t0.size)
	runner.memcpy_d2h(tsc_t0, sym_tsc_t0, 0, 0, Px, Py, 3,\
	    streaming=False, data_type=MemcpyDataType.MEMCPY_16BIT, order=MemcpyOrder.ROW_MAJOR, nonblock=False)
	tsc_t0 = tsc_t0.reshape(Py, Px, 3)
	
	print("step 7: get end times")
	tsc_t1 = np.zeros(Px*Py*3, np.uint32)
	runner.memcpy_d2h(tsc_t1, sym_tsc_t1, 0, 0, Px, Py, 3,\
	    streaming=False, data_type=MemcpyDataType.MEMCPY_16BIT, order=MemcpyOrder.ROW_MAJOR, nonblock=False)
	tsc_t1 = tsc_t1.reshape(Py, Px, 3)
	
	tsc_start = convert_tsc(tsc_t0)
	tsc_end = convert_tsc(tsc_t1)
	tsc_total = tsc_end - tsc_start
	print("Times = ", tsc_total)
	max_time_step = np.max(tsc_total)
	print("Max Step Time = ", max_time_step)
	total_time += int(max_time_step)
	print("Total time = ", total_time)

	if args.img:
		os.makedirs("img", exist_ok=True)
		plt.imshow(A_last, cmap='viridis', interpolation='nearest')
		# Add a colorbar
		plt.colorbar()
		# Save the figure to a file
		plt.savefig(f"img/iter_{i}.png", dpi=300, bbox_inches='tight')
		# Close the figure to free memory
		plt.close()

	

runner.stop()

eq = np.array_equal(A_sorted, A_last)
print("PERF_RESULT: ", json.dumps({
	"Px": Px,
	"Py": Py,
	"dx": dx,
	"dy": dy,
	"total_time": int(total_time),
	"iters": i,
	"success": bool(eq)
}))

np.testing.assert_equal(A_sorted, A_last)

print("SUCCESS")
