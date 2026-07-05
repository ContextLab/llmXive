cmake_minimum_required(VERSION 3.10)
project(benchmark_suite CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Executable for verify_layout
add_executable(verify_layout verify_layout.cpp)
target_compile_options(verify_layout PRIVATE -O3 -march=native)

# Executable for main benchmark (placeholder for now, will be implemented in T014)
# add_executable(benchmark_runner main.cpp)
# target_compile_options(benchmark_runner PRIVATE -O3 -march=native)
