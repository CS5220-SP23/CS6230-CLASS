#ifndef UTILS_CUH
#define UTILS_CUH

#include "common.h"
#include <thrust/device_ptr.h>
#include <thrust/host_vector.h>

namespace spmv {

namespace utils {

template <typename T>
void print_device_buffer(size_t n, T * d_buf)
{
    thrust::device_ptr<T> d_buf_ptr(d_buf);
    thrust::host_vector<T> h_buf(d_buf_ptr, d_buf_ptr+n);
    std::for_each(h_buf.begin(), h_buf.end(), [](const T& elem) { std::cout<<elem<<std::endl;});
}

template <typename T>
void write_device_buffer(size_t n, T * d_buf, std::ofstream& ofs)
{
    thrust::device_ptr<T> d_buf_ptr(d_buf);
    thrust::host_vector<T> h_buf(d_buf_ptr, d_buf_ptr+n);
    std::for_each(h_buf.begin(), h_buf.end(), [&](const T& elem) { ofs<<elem<<std::endl;});
}

}
}


#endif
