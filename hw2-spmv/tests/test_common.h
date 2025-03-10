
#ifndef TEST_COMMON_H
#define TEST_COMMON_H

#include <vector>
#include <fstream>
#include <iostream>
#include <chrono>
#include <map>
#include <algorithm>
#include <numeric>
#include <unordered_set>
#include <random>
#include <cassert>


#include <cuda.h>
#include <cuda_runtime.h>

#include <cublas_v2.h>
#include <cusparse_v2.h>

#include <cub/cub.cuh>

#include "colors.h"
#include "utils.cuh"


#define CUDA_CHECK(call) {                                                 \
    cudaError_t err = call;                                                \
    if (err != cudaSuccess) {                                              \
        std::cerr << "CUDA Error: " << cudaGetErrorString(err) << " ("     \
                  << __FILE__ << ":" << __LINE__ << ")" << std::endl;      \
        exit(err);                                                         \
    }                                                                      \
}

#define CUSPARSE_CHECK(call) do {                                    \
    cusparseStatus_t err = call;                                     \
    if (err != CUSPARSE_STATUS_SUCCESS) {                            \
        fprintf(stderr, "cuSPARSE error in file '%s' in line %i : %s.\n", \
                __FILE__, __LINE__, cusparseGetErrorString(err));    \
        exit(EXIT_FAILURE);                                          \
    }                                                                \
} while(0)

#define EPS 0.001

namespace testing {


/***************************************************************************
 *                                                                         *
 *                           MATRIX AND VECTOR INITIALIZATION              *
 *                                                                         *
 ***************************************************************************/
std::random_device rd;
std::mt19937 gen(rd());

template <typename T>
void init_random_buffer(std::vector<T>& buf,
                        const T lower, 
                        const T upper)
{
    std::uniform_real_distribution<T> distr(lower, upper);
    std::generate(buf.begin(), buf.end(), [&]()
    {
        T elem = distr(gen);
        return elem;
    }); 

}


template <typename T>
void init_dense_vec(const size_t n,
                    T ** d_vals)
{
    std::vector<T> h_vals(n);
    init_random_buffer(h_vals, static_cast<T>(1.0), static_cast<T>(10.0));

    CUDA_CHECK(cudaMalloc(d_vals, sizeof(T)*n));
    CUDA_CHECK(cudaMemcpy(*d_vals, h_vals.data(), sizeof(T)*n, cudaMemcpyHostToDevice));
}


template <typename T>
cusparseDnVecDescr_t cusparse_dense_vec(T* d_buf, size_t n)
{
    cusparseDnVecDescr_t v;
    CUSPARSE_CHECK(cusparseCreateDnVec(&v, n, d_buf, CUDA_R_32F));
    return v;
}


/***************************************************************************
 *                                                                         *
 *                           PROFILING                                     *
 *                                                                         *
 ***************************************************************************/

std::map<std::string, cudaEvent_t> stimes;
std::map<std::string, cudaEvent_t> etimes;

std::map<std::string, size_t> gflops;
std::map<std::string, float> times;

void start_timer(const char * label)
{
    std::string label_str(label);
    cudaEvent_t start, end;

    stimes[label_str] = start;
    etimes[label_str] = end;

    cudaEventCreate(&stimes[label_str]);
    cudaEventCreate(&etimes[label_str]);

    cudaEventRecord(stimes[label_str]);
}


void end_timer(const char * label)
{
    std::string label_str(label);

    cudaEventRecord(etimes[label_str]);
    cudaEventSynchronize(etimes[label_str]);

    float t = 0;
    cudaEventElapsedTime(&t, stimes[label_str], etimes[label_str]);

    times[label] = t;

    cudaEventDestroy(stimes[label_str]);
    cudaEventDestroy(etimes[label_str]);
}


void measure_gflops(const char * label, size_t flops)
{
    std::string label_str(label);
    size_t gflops_per_sec = (flops / 1e9) / (times[label] / 1e3);
    gflops[label] = gflops_per_sec;
}


void print_time(const char * label)
{
    std::string label_str(label);
    std::cout<<BRIGHT_RED<<"["<<label_str<<"]: "<<times[label_str]/1e3<<"s"<<RESET<<std::endl;
}


void print_gflops(const char * label)
{
    std::string label_str(label);
    std::cout<<BRIGHT_BLUE<<"["<<label_str<<"]: "<<gflops[label_str]<<" gflops/s"<<RESET<<std::endl;
}


}

#endif
