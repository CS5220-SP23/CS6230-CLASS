from cerebras.sdk.sdk_debug_pe_symbol_dump import PESymbolDump
from cerebras.elf.cself import ELFMemory, ELFLoader
from glob import glob
import json
import numpy as np
import pandas as pd
import string
import os

# CLI Params
compdir = './out'
sim_out_path = './core.out'

# Globals
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)

CONNECTED = 0
BROKEN = 1
BORDER = 2

DIR_INV = {
    "NORTH": "SOUTH",
    "SOUTH": "NORTH",
    "EAST": "WEST",
    "WEST": "EAST",
    "RAMP": "RAMP",
}


# Impl
coords_to_elf = {}
coords_to_debug = {}
coords_to_updated_elf = {}
coords_to_updated_yamls = {}


elf_glob = f"{compdir}/bin/out_[0-9]*.elf"
elf_paths = glob(elf_glob)
print(f"elf glob: {elf_glob}")

single_elf = ELFLoader(elf_paths[0])
full_fabric_dims = single_elf.get_fabric_dimensions()
print(f"FULL FABRIC: {full_fabric_dims}")
for elf in elf_paths:
    mem = ELFMemory(elf)
    for coord in mem.iter_coordinates():
        coords_to_elf[coord] = elf
        coords_to_debug[coord] = json.loads(
            mem.get_section(".pe_debug_info"))

offset_height = 99999
offset_width = 99999
fabric_width = 0
fabric_height = 0
for i, j in coords_to_elf.keys():
    fabric_width = max(fabric_width, i)
    offset_width = min(offset_width, i)
    fabric_height = max(fabric_height, j)
    offset_height = min(offset_height, j)
# assert offsets[0] == offset_width, "should match offset width from elf"
# assert offsets[1] == offset_height,  "should match offset height from elf"
fabric_width += 1
fabric_height += 1
fabric_width += offset_width
fabric_height += offset_height
fabric_size = (fabric_height, fabric_width)
print(f"Full fabric size: {fabric_size}, offset sizes, height: {offset_height}, width: {offset_width}")
offsets = (offset_width, offset_height)

coutns = np.zeros((fabric_height, fabric_width), dtype=int)
coords_to_debug_info = np.zeros(
    (fabric_height, fabric_width), dtype=object)
seen_types = {}
coords_to_file = np.zeros(
    (fabric_height, fabric_width), dtype=object)
coords_to_file[:] = "unmapped"
for coord in coords_to_debug.keys():
    l = coords_to_debug[coord]
    if l["filename"] not in seen_types:
        seen_types[l["filename"]] = len(seen_types.items())
    coutns[coord[1], coord[0]] += 1
    coords_to_debug_info[coord[1], coord[0]] = l
    coords_to_debug_info[coord[1], coord[0]]["color_info_dict"] = {
        ci["id"]: ci for ci in l['color_info']}
    coords_to_file[coord[1], coord[0]] = l["filename"]

def _route_has_link(col, row, color_id, dir, rxtx):
    # TODO(lbb): Find out in what case this happens.
    assert rxtx in ("rx", "tx")
    if (col < offsets[0] or row < offsets[1]):
        return BORDER
    if (col+offsets[0] >= fabric_size[1]):
        return BORDER
    if (row+offsets[1] >= fabric_size[0]):
        return BORDER

    if not isinstance(coords_to_debug_info[row, col], dict):
        # print(f"Weird type: {type(coords_to_debug_info[row, col])}")
        return BORDER

    if color_id in coords_to_debug_info[row, col]["color_info_dict"]:
        if rxtx not in coords_to_debug_info[row, col]["color_info_dict"][color_id]:
            print(
                f"rxtx: {rxtx} not in {coords_to_debug_info[row, col]['color_info_dict'][color_id]}")
            return BROKEN
        if dir.lower() in coords_to_debug_info[row, col]["color_info_dict"][color_id][rxtx]:
            return CONNECTED
    return BROKEN

def _route_connected(col, row, color_id, rxtx):
    assert rxtx in ("rx", "tx")
    ci = coords_to_debug_info[row, col]["color_info_dict"][color_id]
    cns = []
    irxtx = {"tx": "rx", "rx": "tx"}[rxtx]
    for dir in ci[rxtx]:
        if dir.upper() == "NORTH":
            cns.append(_route_has_link(
                col, row-1, color_id, DIR_INV["NORTH"], irxtx))
        elif dir.upper() == "EAST":
            cns.append(_route_has_link(
                col+1, row, color_id, DIR_INV["EAST"], irxtx))
        elif dir.upper() == "SOUTH":
            cns.append(_route_has_link(
                col, row+1, color_id, DIR_INV["SOUTH"], irxtx))
        elif dir.upper() == "WEST":
            cns.append(_route_has_link(
                col-1, row, color_id, DIR_INV["WEST"], irxtx))
        elif dir.upper() == "RAMP":
            cns.append(CONNECTED)
    return cns

def _routing(col, row, unicode=False):
    di = coords_to_debug_info[row, col]
    ttx = {
        "NORTH": '⬆' if unicode else "N",
        "EAST": '⮕' if unicode else "E",
        "SOUTH": '⬇' if unicode else "S",
        "WEST": '⬅' if unicode else "W",
        "RAMP": 'R',
    }
    trx = {
        "NORTH": '⬇' if unicode else "N",
        "EAST": '⬅' if unicode else "E",
        "SOUTH": '⬆' if unicode else "S",
        "WEST": '⮕' if unicode else "W",
        "RAMP": 'R',
    }
    bash_color_conn = {
        CONNECTED: "\033[0m",
        BROKEN: "\033[31m",
        BORDER: "\033[33m",
    }
    #print(di)
    routable_colors_count = 24
    print(
        f"Colors used: {len(di['color_info'])}/{routable_colors_count} ({len(di['color_info'])/float(routable_colors_count):.1%})")
    print(f"{'ID':<2}  {'Rx':<4}    {'TX':<4}  {'Names':>20}")
    for ci in di['color_info']:
        color_id = ci["id"]
        has_rxtx = 'rx' in ci
        names = ""
        if "known_names" in ci:
            names = " ".join(ci["known_names"])
        if has_rxtx:
            rx = "".join(bash_color_conn[c]+trx[x.upper()]+"\033[0m" for x, c in zip(
                ci["rx"], _route_connected(col, row, color_id, "rx")))
            tx = "".join(bash_color_conn[c]+ttx[x.upper()]+"\033[0m" for x, c in zip(
                ci["tx"], _route_connected(col, row, color_id, "tx")))
            rx += " " * (4-len(ci["rx"]))
            tx += " " * (4-len(ci["tx"]))
            print(f"{color_id:<2}  {rx} -> {tx}  {names:>20}")
        else:
            print(f"{color_id:<2}  ------------  {names:>20}")


def _is_pos_in_kernel(col, row):
    if (col < offsets[0] or row < offsets[1]):
        return False
    if (col+offsets[0] >= fabric_size[1]):
        return False
    if (row+offsets[1] >= fabric_size[0]):
        return False
    return True


def _mapview(col, row):
    sk = sorted(seen_types.keys())
    m = {f: i for i, f in enumerate(sk)}
    m_reversed = {i: f for i, f in enumerate(sk)}
    alphabet = string.printable
    linelength = fabric_size[0]
    for i in range(fabric_size[0]):
        for j in range(fabric_size[1]):
            focus = (j == col and i == row)
            if focus:
                print("\033[41m", end="")
            if not _is_pos_in_kernel(j, i) or coords_to_debug_info[i, j] == 0:
                print("░", end="")
            else:
                print(
                    alphabet[m[coords_to_debug_info[i, j]["filename"]]], end="")
            if focus:
                print("\033[0m", end="")
        print("  ", end="")
        if i < len(m):
            print(f"{alphabet[i]:>2}: {m_reversed[i]}", end="")
        print()
    if fabric_size[0] < len(m):
        for j in range(fabric_size[0], len(m), 1):
            print(" " * linelength)
            print("  ", end="")
            print(f"{alphabet[j]:<2}: {m_reversed[j]}", end="")
            print()

def _d(col, row):
    print(f"================ ({col:2}, {row:2}) ================")
    loader = ELFLoader(coords_to_elf[col, row])
    print(
        f"\033[1;31mPE[col={col}, row={row}]: {coords_to_debug_info[row, col]['filename']}\033[0m")

    print("Routing:")
    _routing(col, row)

    print("Position:")
    _mapview(col, row)
    print(f"==========================================")

for coord in sorted(coords_to_elf.keys()):
	_d(*coord)
