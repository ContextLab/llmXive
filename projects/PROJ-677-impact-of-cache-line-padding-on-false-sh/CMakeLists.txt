cmake_minimum_required(VERSION 3.10)
project(FalseSharingBenchmark CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Default to Release build if not specified
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native")

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/code/benchmark)

# Add benchmarks executable
add_executable(benchmark
    code/benchmark/main.cpp
    code/benchmark/verify_layout.cpp
)

# Link pthread
find_package(Threads REQUIRED)
target_link_libraries(benchmark Threads::Threads)
