cmake_minimum_required(VERSION 3.14)
project(CompilerOptBenchmarks LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Build MatMul kernel
add_executable(matmul_kernel kernels/matmul.cpp)

# Default optimization level can be overridden by CMAKE_CXX_FLAGS
# e.g., cmake -DCMAKE_CXX_FLAGS="-O3" ..
target_compile_options(matmul_kernel PRIVATE $ENV{CXX_FLAGS})
