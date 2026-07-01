#!/bin/bash
# Build script for cache padding benchmark
# Initializes C++17 build system and compiles benchmark executable

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
BENCHMARK_DIR="$PROJECT_ROOT/code/benchmark"

echo "=== Cache Padding Benchmark Build System ==="
echo "Project Root: $PROJECT_ROOT"
echo "Build Directory: $BUILD_DIR"

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
echo "Configuring CMake..."
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
      ..

# Build
echo "Building benchmark executable..."
cmake --build . --config Release

# Verify binary exists
if [ -f "$BUILD_DIR/bin/benchmark" ]; then
    echo "Build successful! Binary location: $BUILD_DIR/bin/benchmark"
    echo "Binary info:"
    ls -lh "$BUILD_DIR/bin/benchmark"
    file "$BUILD_DIR/bin/benchmark"
else
    echo "ERROR: Binary not found at expected location"
    exit 1
fi

echo "=== Build Complete ==="
