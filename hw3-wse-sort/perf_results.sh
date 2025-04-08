#!/bin/bash

set -euo pipefail

cycle_times=()
all_success=1


# Header
printf "%-5s %-5s %-5s %-5s %-10s %-10s %-10s\n" "Px" "Py" "dx" "dy" "total_time" "norm_time" "success"

# Loop through all JSON files (you can adjust the pattern if needed)
for file in perflogs/*; do
    json=$(grep '^PERF_RESULT:' "$file" | sed 's/^PERF_RESULT: //')
    px=$(echo "$json" | jq '.Px')
    py=$(echo "$json" | jq '.Py')
    dx=$(echo "$json" | jq '.dx')
    dy=$(echo "$json" | jq '.dy')
    total_time=$(echo "$json" | jq '.total_time')
    success=$(echo "$json" | jq '.success')
    if [ $success == "false" ] ; then
         all_success=0
    fi

    product=$(echo "$px * $py * $dx * $dy" | bc)
    normalized_total_time=$(echo "$total_time / $product" | bc -l)
    printf "%-5d %-5d %-5d %-5d %-10d %-10.2f %-10s\n" "$px" "$py" "$dx" "$dy" "$total_time" "$normalized_total_time" "$success"


    cycle_times+=($normalized_total_time)
done

geometric_mean() {
    local arr=("$@")
    local n=${#arr[@]}

    # Initialize product to 1
    local product=1

    # Multiply all elements
    for num in "${arr[@]}"; do
        product=$(echo "$product * $num" | bc -l)
    done

    # Calculate the nth root using bc
    local result=$(echo "e(l($product)/$n)" | bc -l)

    echo "$result"
}

if [ $all_success == 1 ] ; then
    gm=$(geometric_mean "${cycle_times[@]}")
    printf "Geometric Mean: %.4f\n" "$gm"
else
    echo -e "\033[31;1;5mA test failed, no geomean\033[0m"
fi

