cmake_minimum_required(VERSION 3.20)
project(cache_padding_benchmark VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimization flags for performance benchmarking
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")
set(CMAKE_CXX_FLAGS_DEBUG "-O0 -g -fsanitize=address,undefined")

# Ensure Release build by default if not specified
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Benchmark executable
add_executable(benchmark
    ../benchmark/main.cpp
    ../benchmark/verify_layout.cpp
    ../benchmark/counter_packed.hpp
    ../benchmark/counter_padded.hpp
)

# Link pthread for multi-threading
find_package(Threads REQUIRED)
target_link_libraries(benchmark PRIVATE Threads::Threads)

# Set output directory
set_target_properties(benchmark PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Installation rule
install(TARGETS benchmark DESTINATION bin)
