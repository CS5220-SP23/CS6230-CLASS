
#include <chrono>
#include <fstream>
#include <iostream>
#include <iomanip>

#include <cuda.h>
#include <cuda_runtime.h>

#include <cublas_v2.h>
#include <cusparse.h>

#include <cub/cub.cuh>

#include "spmv.cuh"
#include "CSR.hpp"
#include "test_common.h"


using namespace testing;
using namespace spmv;

typedef float D;
typedef uint32_t I;


template <typename D>
bool nearly_equal(D a, D b)
{
	D epsilon = 1e-5;
    if (a == b) return true;
    return std::abs(a - b)  < epsilon;
}


template <typename Matrix, typename D>
void check_correctness(Matrix & csr_A, D * d_x, D * d_y, cusparseSpMatDescr_t A, 
                        cusparseDnVecDescr_t x, cusparseDnVecDescr_t y)
{
    cusparseHandle_t cusparseHandle;
    CUSPARSE_CHECK(cusparseCreate(&cusparseHandle));

    const float alpha = 1.0;
    const float beta = 0.0;

    auto m = csr_A.get_rows();
    auto n = csr_A.get_cols();
    auto nnz = csr_A.get_nnz();

    size_t buf_size;
    void * buf;

    CUSPARSE_CHECK(cusparseSpMV_bufferSize(cusparseHandle,
                                            CUSPARSE_OPERATION_NON_TRANSPOSE,
                                            &alpha, A, x,
                                            &beta, y,
                                            CUDA_R_32F,
                                            CUSPARSE_SPMV_CSR_ALG2,
                                            &buf_size));

    CUDA_CHECK(cudaMalloc(&buf, buf_size));
    CUSPARSE_CHECK(cusparseSpMV(cusparseHandle,
                                CUSPARSE_OPERATION_NON_TRANSPOSE,
                                &alpha, A, x,
                                &beta, y,
                                CUDA_R_32F,
                                CUSPARSE_SPMV_CSR_ALG2,
                                buf));

    CUDA_CHECK(cudaDeviceSynchronize());

    CUDA_CHECK(cudaFree(buf));
    D * h_correct = new D[m];
    CUDA_CHECK(cudaMemcpy(h_correct, d_y, sizeof(D)*m, cudaMemcpyDeviceToHost));

    CUDA_CHECK(cudaMemset(d_y, 0, sizeof(D)*m));

    SpMV_wrapper(csr_A, d_x, d_y);

    D * h_computed = new D[m];
    CUDA_CHECK(cudaMemcpy(h_computed, d_y, sizeof(D)*m, cudaMemcpyDeviceToHost));

    for (size_t i=0; i<m; i++) 
    {
        if (!nearly_equal(h_computed[i], h_correct[i]))
        {
            std::cout<<RED<<"Error: got "<<h_computed[i]<<" expected "<<h_correct[i]<<RESET<<std::endl;
            exit(1);
        }
    }
    std::cout<<GREEN<<"Correctness for SpMV passed!"<<RESET<<std::endl;


    CUSPARSE_CHECK(cusparseDestroy(cusparseHandle));

    delete[] h_correct;
    delete[] h_computed;
}


int main(int argc, char ** argv)
{
    cusparseHandle_t cusparseHandle;
    CUSPARSE_CHECK(cusparseCreate(&cusparseHandle));
    const size_t n_iters = 100;

    if (argc != 2)
    {
        std::cerr<<"Usage: ./test_spmv <path/to/mat>"<<std::endl;
        exit(1);
    }


    std::string matname = std::string(argv[1]);

    std::cout<<YELLOW<<"Reading in "<<matname<<RESET<<std::endl;
    CSR<D, I> csr_A(matname, cusparseHandle);
    std::cout<<GREEN<<"Done!"<<RESET<<std::endl;

    auto A = csr_A.to_cusparse_spmat();

    auto m = csr_A.get_rows();
    auto n = csr_A.get_cols();
    auto nnz = csr_A.get_nnz();

    D * d_x;
    init_dense_vec(n, &d_x);

    D * d_y;
    CUDA_CHECK(cudaMalloc(&d_y, sizeof(D)*m));
    CUDA_CHECK(cudaMemset(d_y, 0, sizeof(D)*m));

    auto x = cusparse_dense_vec(d_x, n);
    auto y = cusparse_dense_vec(d_y, m);

    /* Correctness check */
    std::cout<<YELLOW<<"Running correctness check"<<matname<<RESET<<std::endl;
    check_correctness(csr_A, d_x, d_y, A, x, y);

    /* Benchmarks */
    std::cout<<YELLOW<<"Running cusparse benchmark"<<matname<<RESET<<std::endl;
    const float alpha = 1.0;
    const float beta = 0.0;

    size_t buf_size;
    void * buf;
    CUSPARSE_CHECK(cusparseSpMV_bufferSize(cusparseHandle,
                                            CUSPARSE_OPERATION_NON_TRANSPOSE,
                                            &alpha, A, x,
                                            &beta, y,
                                            CUDA_R_32F,
                                            CUSPARSE_SPMV_CSR_ALG2,
                                            &buf_size));
    CUDA_CHECK(cudaMalloc(&buf, buf_size));
    
    /* Benchmark cuSPARSE */
    const char * label_cusparse = "SpMV_cusparse";

    start_timer(label_cusparse);
    for (int i=0; i<n_iters; i++) {
        CUSPARSE_CHECK(cusparseSpMV(cusparseHandle,
                                    CUSPARSE_OPERATION_NON_TRANSPOSE,
                                    &alpha, A, x,
                                    &beta, y,
                                    CUDA_R_32F,
                                    CUSPARSE_SPMV_CSR_ALG2,
                                    buf));
    }
    end_timer(label_cusparse);

    CUDA_CHECK(cudaFree(buf));
    measure_gflops(label_cusparse, 2*nnz*n_iters);

    print_time(label_cusparse);
    print_gflops(label_cusparse);


    /* Benchmark student implementation */
    std::cout<<YELLOW<<"Running student benchmark"<<matname<<RESET<<std::endl;
    const char * label_spmv_student = "SpMV_student";

    start_timer(label_spmv_student);
    for (int i=0; i<n_iters; i++) {
        SpMV_wrapper(csr_A, d_x, d_y);
    }
    end_timer(label_spmv_student);
    measure_gflops(label_spmv_student, 2*nnz*n_iters);

    print_time(label_spmv_student);
    print_gflops(label_spmv_student);

    CUSPARSE_CHECK(cusparseDestroySpMat(A));
    CUSPARSE_CHECK(cusparseDestroyDnVec(x));
    CUSPARSE_CHECK(cusparseDestroyDnVec(y));


    CUDA_CHECK(cudaFree(d_x));
    CUDA_CHECK(cudaFree(d_y));

    CUSPARSE_CHECK(cusparseDestroy(cusparseHandle));


    return 0;
}
