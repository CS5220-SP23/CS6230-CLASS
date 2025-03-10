# SpMV Exercise #
Sparse matrix-vector multiply (SpMV) is a fundamental sparse primitive. Given an `m x n` sparse matrix `A` and a dense input vector `x`, SpMV computes the matrix-vector product `y = Ax`.
SpMV has numerous applications in areas such as graph analytics, clustering, and iterative solvers, and it is often the bottleneck in these applications. 
The goal of this homework is to implement and benchmark a simple parallel SpMV kernel with CUDA.


## Build Instructions ##
To build the driver program, run the following

`module load cmake/3.30.2` (on the Perlmutter)

`mkdir build && cd build`

`cmake ..`

`make test_spmv`

This will generate a binary called `test_spmv`, which can be run with a command like this

`./test_spmv /path/to/matrix`

where `/path/to/matrix` is a relative path to a matrix stored in matrix market (`.mtx`) format.

The `test_spmv` executable does two things.
First, it will run a correctness check that compares the output of your SpMV kernel to the output of the SpMV kernel found in the [cuSPARSE library](https://docs.nvidia.com/cuda/cusparse/contents.html). 
Second, it runs a simple benchmark that compares the throughput in terms of GFLOPS/s of your SpMV kernel to the throughput of cuSPARSE's SpMV kernel.


## Running Benchmarks ## 

Once you have built the executable, please run `sh get_matrices.sh`, which will fetch two large test matrices (`delaunay_n22`, `stomach`) from the [SuiteSparse matrix collection](https://sparse.tamu.edu/) and place them in the `matrices` directory.
These two matrices can be used to benchmark the computational throughput of your implementation relative to cuSPARSE.
Additionally, the `matrices` directory contains a small matrix called `n16.mtx`, which can be used for debugging.

If you would like to benchmark your implementation on other test matrices other than the ones obtained by `get_matrices.sh`, you can find a large collection of them on [SuiteSparse](https://sparse.tamu.edu/).
To fetch a specific matrix from SuiteSparse, left-click the `Matrix Market` button next to the matrix, copy the link referenced by that button, then run `wget <link>` to fetch a tarball containing the matrix. Then, you can `tar -xzf </path/to/tarball>` to decompress the matrix.

## Assignment Expectations ##

To complete this assignment, the following things are required.

1. You must implement and SpMV kernel that runs on the GPU and passes correctness tests for the `n16`, `stomach` and `delaunay_n22` matrices. 

2. You must compare the throughput in terms of GFLOPS/s of your SpMV kernel to that of cuSPARSE for at least the `stomach` and `delaunay_n22` matrices. For this, you can simply use the numbers reported by `test_spmv`. Note that you do not have to beat or match theperformance of cuSPARSE. Benchmarking additional large matrices is encouraged but not required. 

## Important Files ## 
The main file that you'll need to work with is `include/spmv.cuh`. This file contains the template SpMV kernel that you'll need to implement. Within this file, there are two importation functions

1. `__global__ void SpMV()` is the actual kernel that performs the SpMV operation on the GPU.

2. `void SpMV_wrapper()` is a simple wrapper function callable from the host that will call the GPU SpMV kernel. 
You can use this function to set anything up or perform any preprocessing steps that are necessary for your implementation to function.

The driver program can be found in `tests/test_spmv.cu`, although you should not have to edit this file at all in order to complete the assignment.


## CSR Data Structure ##
Your implementation will need to function with the sparse matrix `A` stored in Compressed Sparse Row (CSR) format.
CSR is a standard compressed storage format used to efficiently store and process large sparse matrices. 

The CSR format uses three arrays `values`, `colinds`, and `rowptrs`.
The `values` array stores the values of the nonzeros in `A`.
The `colinds` array stores the column index of each nonzero in `A`. It is the same length as the `values` array.
Finally, the `rowptrs` array stores the start index of each row of `A` in `values` and `colinds`. For example, if `rowptrs[i] = 6`, then `values[6]` contains the first nonzero element in the ith row of `A`, and `colinds[6]` contains the column index of that element.
Additionally, if `rowptrs[i+1] = 11`, then the range `values[6:11]` contains all the nonzeros in the ith row of `A`.

For more information on CSR, see [Wikipedia](https://en.wikipedia.org/wiki/Sparse_matrix#Compressed_sparse_row_(CSR,_CRS_or_Yale_format)).

In this repo, `include/CSR.hpp` defines a class that can be used to store a sparse matrix using the CSR storage format. 


## References ## 

These are some optional references you can look at for inspiration/more information.

* Bell, Nathan, and Michael Garland. "Implementing sparse matrix-vector multiplication on throughput-oriented processors." Proceedings of the conference on high performance computing networking, storage and analysis. 2009. [https://doi.org/10.1145/1654059.1654078](https://doi.org/10.1145/1654059.1654078)

* Ashari, Arash, et al. "Fast sparse matrix-vector multiplication on GPUs for graph applications." SC'14: Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis. IEEE, 2014. [https://dl.acm.org/doi/10.14778/1938545.1938548](https://dl.acm.org/doi/10.14778/1938545.1938548)

* [cuSPARSE SpMV API](https://docs.nvidia.com/cuda/cusparse/#cusparsespmv)
