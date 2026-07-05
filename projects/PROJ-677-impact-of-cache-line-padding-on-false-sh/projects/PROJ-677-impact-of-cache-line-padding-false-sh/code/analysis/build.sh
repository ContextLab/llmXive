#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"
BUILD_DIR="$PROJECT_ROOT/build"

echo "=== Building Cache Padding Benchmark ==="
echo "Project Root: $PROJECT_ROOT"
echo "Build Dir: $BUILD_DIR"

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
echo "Configuring CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
echo "Compiling..."
make -j$(nproc)

# Verify executables exist
if [[ ! -x "benchmark" ]]; then
    echo "ERROR: benchmark executable not found!"
    exit 1
fi

if [[ ! -x "verify_layout" ]]; then
    echo "ERROR: verify_layout executable not found!"
    exit 1
fi

echo "=== Build Complete ==="
echo "Executables available in: $BUILD_DIR"
echo "Run benchmark: $BUILD_DIR/benchmark"
echo "Run verification: $BUILD_DIR/verify_layout"