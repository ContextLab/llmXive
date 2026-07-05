cmake_minimum_required(VERSION 3.16)
project(cache_padding_benchmark LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimization flags for release builds
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")

# Benchmark executable
add_executable(benchmark ../benchmark/main.cpp)
target_include_directories(benchmark PRIVATE ../benchmark)

# Verification utility
add_executable(verify_layout ../benchmark/verify_layout.cpp)
target_include_directories(verify_layout PRIVATE ../benchmark)

# Install targets
install(TARGETS benchmark verify_layout DESTINATION bin)