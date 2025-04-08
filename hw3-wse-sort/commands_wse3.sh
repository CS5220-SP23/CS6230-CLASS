#!/usr/bin/env bash

Px=${1:-3}
Py=${2:-2}
dx=${3:-8}
dy=${3:-8}
shift 4
echo "$Px $Py $dx $dy"

cslc --arch=wse3 ./layout.csl --fabric-dims=$((2 * 4 + $Px)),$((2 * 1 + $Py)) --fabric-offsets=4,1 \
--params=\
Px:${Px},\
Py:${Py},\
dx:${dx},\
dy:${dy} \
-o out --memcpy --channels=1 --width-west-buf=0 --width-east-buf=0

if [ -v PERF ]; then
  cs_python -u run.py --name out "$@" | tee perflogs/${Px}_${Py}_${dx}_${dy}.log
else
  cs_python run.py --name out "$@"
fi

