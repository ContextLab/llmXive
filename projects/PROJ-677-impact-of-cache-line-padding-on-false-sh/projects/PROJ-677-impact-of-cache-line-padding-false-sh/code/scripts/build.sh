#!/bin/bash
set -e

# Project root relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BENCHMARK_DIR="$PROJECT_ROOT/code/benchmark"
BUILD_DIR="$PROJECT_ROOT/code/benchmark/build"

echo "=== Building Cache Line Padding Benchmark ==="
echo "Project Root: $PROJECT_ROOT"
echo "Benchmark Dir: $BENCHMARK_DIR"

# Create build directory if it doesn't exist
mkdir -p "$BUILD_DIR"

# Configuration for compilation
CXX="${CXX:-g++}"
CXXFLAGS="-std=c++17 -O3 -march=native -Wall -Wextra -Werror"

# Source files to compile
MAIN_SRC="$BENCHMARK_DIR/main.cpp"
VERIFY_SRC="$BENCHMARK_DIR/verify_layout.cpp"

# Check if source files exist
if [[ ! -f "$MAIN_SRC" ]]; then
    echo "ERROR: main.cpp not found at $MAIN_SRC"
    exit 1
fi

if [[ ! -f "$VERIFY_SRC" ]]; then
    echo "ERROR: verify_layout.cpp not found at $VERIFY_SRC"
    exit 1
fi

echo "Compiling verify_layout.cpp..."
if ! $CXX $CXXFLAGS -I"$BENCHMARK_DIR" "$VERIFY_SRC" -o "$BUILD_DIR/verify_layout" 2>&1; then
    echo "ERROR: Compilation of verify_layout.cpp failed"
    exit 1
fi
echo "SUCCESS: verify_layout.cpp compiled"

echo "Compiling main.cpp..."
if ! $CXX $CXXFLAGS -I"$BENCHMARK_DIR" "$MAIN_SRC" -o "$BUILD_DIR/benchmark_runner" 2>&1; then
    echo "ERROR: Compilation of main.cpp failed"
    exit 1
fi
echo "SUCCESS: main.cpp compiled"

echo "=== Build Complete ==="
echo "Executables available in: $BUILD_DIR"
ls -lh "$BUILD_DIR"

# Verify executables were created
if [[ ! -x "$BUILD_DIR/verify_layout" ]] || [[ ! -x "$BUILD_DIR/benchmark_runner" ]]; then
    echo "ERROR: One or more executables are missing or not executable"
    exit 1
fi

echo "All builds successful. Ready to run benchmarks."
exit 0
