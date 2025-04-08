# CS6230 Homework: Wafer Scale Engine Sorting

## Installation:

```bash
$CFS/m4341/cs6230/cbsdk-1.3.0/install.sh
echo "export PATH=$PATH:${CFS}/m4341/cs6230/cbsdk-1.3.0" >> ~/.bashrc
```

### Makefile overview:

You can add configurations to the Makefile, the testcases are a convinience. Perf is used for evaluation.

* `make small` – for small configuration.
* `make hskew` – for horizontal skew configuration.
* `make vskew` – for vertical skew configuration.
* `make pelarge` – for large PE configuration.
* `make perf` – for performance testing.
* `make clean` – to clean up generated files.
* `make debug` – to run the debug script.


## Homework 1: Routing

To verify this assingment use `make run; make debug`. The `run` command
is not supposed to pass, yet.

### HW1.0 - Assigning Correct Colors

-   Implement a checkerboard pattern to alternate between RX and TX
    routes.
-   This pattern will ensure that RX and TX routes are distinguishable
    through unique color assignments.

### HW1.1 - Defining Routes for Assigned Colors

-   After correctly assigning colors, you will proceed to define the
    routes associated with each color.
-   Use the `@set_local_color_config` function to assign the routes for
    RX and TX based on their respective colors.


## Homework 2: Sorting

At the end of this assignment you can expect `make run` to pass.

### HW2.0 - Implementing Column Sorting
-   Implement the communication functionality within the `col_sort`
    function.
-   The goal here is to ensure that the elements in each column are
    sorted correctly.
-   The sort direction is ASC from NORTH to SOUTH.
-   You can verify the correctness of your sorting implementation by
    using the `–img` flag to visualize the sorted output.
    - The output can be found in `img/*`
-   To speed up testing and debugging, use the `-–iters` flag with a low
    value, reducing the number of iterations and allowing quicker
    verification of your implementation.

### HW2.1 - Implementing Row Sorting

-   After completing the column sorting, invoke the `row_sort` task.
-   This function should be executed following the column sort to sort
    the elements in rows, completing the two-dimensional sorting
    process. However, if you are not bound to any particular order.
-   The row sorting ensures that the final arrangement of elements is
    sorted both by columns and rows, providing a fully organized system.
-   Hint: Iters needs to be sufficiently high for the sorting to
    terminate and not abort preemptively.

## Homework 3: Optimization

### Optimization Considerations and Suggestions

You will only be evaluated on the final cycletime! You can
increase/remove phases or change the algorithm in any way.

-   **Improving the Local Sorting Algorithm:**
    -   The current local sorting algorithm (similar to bubble sort) is
        inefficient and slow.
    -   Explore alternative, faster sorting algorithms to improve the
        speed of sorting operations.
-   **Optimizing Communication Between Processing Elements (PEs):**
    -   Currently, communication between PEs is handled sequentially,
        one-by-one, which can create delays.
    -   Investigate ways to speed up communication, such as enabling
        parallel communication or adopting more efficient data transfer
        methods.
-   **Introducting Halo Communication:**
    -   Improve the communication and latency by introducing a halo exchange.
-   **Optimizing DSD-\>DSR Reloads:**
    -   Frequent reloads between DSD (Data Storage Device) and DSR (Data
        Storage Register) can create inefficiencies.
    -   To improve performance, try keeping the DSR alive by using the
        `@load_to_dsr` function, which allows you to retain data in the
        DSR and avoid repeated reloads, enhancing overall efficiency.
-   **Algorithmic choice:**
    -   We changed the definition of the shearsort algorithm to only do
        partial row/col sorts. There might be better hyperparameters to
        converge faster.
    -   Consider if another sorting algorithm is better suited.
