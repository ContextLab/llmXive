#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"
BUILD_DIR="$SCRIPT_DIR/build"
BIN_DIR="$BUILD_DIR/bin"

echo "=== Building Cache Line Padding Benchmark ==="
echo "Project Root: $PROJECT_ROOT"
echo "Build Dir: $BUILD_DIR"

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Run CMake configuration
echo "Configuring with CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
echo "Compiling..."
make -j$(nproc)

# Verify executables exist
if [[ ! -f "$BIN_DIR/benchmark" ]] || [[ ! -f "$BIN_DIR/verify_layout" ]]; then
    echo "ERROR: Build failed. Executables not found."
    exit 1
fi

echo "=== Build Successful ==="
echo "Executables available in: $BIN_DIR"
echo "Run verify_layout: $BIN_DIR/verify_layout"
echo "Run benchmark: $BIN_DIR/benchmark"
