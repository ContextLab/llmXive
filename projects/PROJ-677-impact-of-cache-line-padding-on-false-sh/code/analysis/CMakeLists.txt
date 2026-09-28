cmake_minimum_required(VERSION 3.17)
project(benchmark_suite LANGUAGES CXX)

# Enforce C++17 standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(-O3 -march=native)
    endif()
endif()

# Include directories for headers
include_directories(${CMAKE_SOURCE_DIR}/../benchmark)

# Benchmark executable (compiled later via build.sh, but defined here for structure)
# Note: The actual compilation logic is handled by build.sh to allow dynamic
# detection of flags and architecture, but CMakeLists.txt serves as the
# formal build system definition.
add_executable(verify_layout
    ../benchmark/verify_layout.cpp
)

# Main benchmark executable (placeholder for structure, actual build via build.sh)
# add_executable(benchmark_main
#     ../benchmark/main.cpp
# )

# Installation rules
install(TARGETS verify_layout DESTINATION bin)
