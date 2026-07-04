cmake_minimum_required(VERSION 3.17)
project(CounterBenchmark LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add benchmark executable
add_executable(benchmark ../benchmark/main.cpp)
target_include_directories(benchmark PRIVATE ../benchmark)

# Add verification utility
add_executable(verify_layout ../benchmark/verify_layout.cpp)
target_include_directories(verify_layout PRIVATE ../benchmark)

# Optimization flags
target_compile_options(benchmark PRIVATE -O3 -march=native)
target_compile_options(verify_layout PRIVATE -O3 -march=native)