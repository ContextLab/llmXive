#!/bin/bash
#
# build.sh - Compile the cache line padding benchmark harness
#
# Usage: ./build.sh
#
# This script compiles:
#   1. verify_layout.cpp -> verify_layout (utility to check memory layout)
#   2. main.cpp -> benchmark_runner (main benchmark executable)
#
# Compiler flags: -O3 -march=native for maximum performance optimization
#

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BENCHMARK_DIR="$PROJECT_ROOT/code/benchmark"
BUILD_DIR="$PROJECT_ROOT/code/benchmark/build"

# Compiler settings
CXX="${CXX:-g++}"
CXXFLAGS="-std=c++17 -O3 -march=native -Wall -Wextra -Werror"

echo "=== Cache Line Padding Benchmark Build System ==="
echo "Project Root: $PROJECT_ROOT"
echo "Benchmark Dir: $BENCHMARK_DIR"
echo "Build Dir: $BUILD_DIR"
echo "Compiler: $CXX"
echo "Flags: $CXXFLAGS"
echo ""

# Create build directory if it doesn't exist
if [ ! -d "$BUILD_DIR" ]; then
    echo "[INFO] Creating build directory: $BUILD_DIR"
    mkdir -p "$BUILD_DIR"
fi

# Check for required source files
VERIFY_LAYOUT_SRC="$BENCHMARK_DIR/verify_layout.cpp"
MAIN_SRC="$BENCHMARK_DIR/main.cpp"

if [ ! -f "$VERIFY_LAYOUT_SRC" ]; then
    echo "[ERROR] verify_layout.cpp not found at: $VERIFY_LAYOUT_SRC"
    echo "[ERROR] Please ensure T005 has been completed and the file exists."
    exit 1
fi

if [ ! -f "$MAIN_SRC" ]; then
    echo "[ERROR] main.cpp not found at: $MAIN_SRC"
    echo "[ERROR] Please ensure T014 has been completed and the file exists."
    exit 1
fi

echo "[INFO] Source files found."
echo ""

# Compile verify_layout.cpp
echo "[BUILD] Compiling verify_layout.cpp..."
VERIFY_LAYOUT_BIN="$BUILD_DIR/verify_layout"
if $CXX $CXXFLAGS -o "$VERIFY_LAYOUT_BIN" "$VERIFY_LAYOUT_SRC"; then
    echo "[SUCCESS] verify_layout compiled successfully: $VERIFY_LAYOUT_BIN"
else
    echo "[ERROR] Compilation of verify_layout.cpp failed!"
    echo "[ERROR] Please check the source code for errors."
    exit 1
fi
echo ""

# Compile main.cpp
echo "[BUILD] Compiling main.cpp..."
BENCHMARK_BIN="$BUILD_DIR/benchmark_runner"
if $CXX $CXXFLAGS -o "$BENCHMARK_BIN" "$MAIN_SRC"; then
    echo "[SUCCESS] main.cpp compiled successfully: $BENCHMARK_BIN"
else
    echo "[ERROR] Compilation of main.cpp failed!"
    echo "[ERROR] Please check the source code for errors."
    exit 1
fi
echo ""

# Verify executables exist and are executable
echo "[VERIFY] Checking executables..."
if [ ! -x "$VERIFY_LAYOUT_BIN" ]; then
    echo "[ERROR] verify_layout binary is not executable!"
    exit 1
fi
if [ ! -x "$BENCHMARK_BIN" ]; then
    echo "[ERROR] benchmark_runner binary is not executable!"
    exit 1
fi

echo "[SUCCESS] All binaries are executable."
echo ""

# Display binary sizes
echo "[INFO] Binary sizes:"
ls -lh "$VERIFY_LAYOUT_BIN" | awk '{print "  " $9 ": " $5}'
ls -lh "$BENCHMARK_BIN" | awk '{print "  " $9 ": " $5}'
echo ""

# Quick validation: run verify_layout to ensure it works
echo "[TEST] Running verify_layout for basic validation..."
if "$VERIFY_LAYOUT_BIN"; then
    echo "[SUCCESS] verify_layout executed without errors."
else
    echo "[WARNING] verify_layout returned a non-zero exit code."
    echo "[WARNING] This may indicate an issue with the binary or system configuration."
fi
echo ""

echo "=== Build Complete ==="
echo "Executables:"
echo "  - $VERIFY_LAYOUT_BIN"
echo "  - $BENCHMARK_BIN"
echo ""
echo "Next steps:"
echo "  - Run verify_layout to check memory layout"
echo "  - Run benchmark_runner with appropriate arguments"
echo "  - Use run_benchmarks.sh to execute the full experiment"
echo ""