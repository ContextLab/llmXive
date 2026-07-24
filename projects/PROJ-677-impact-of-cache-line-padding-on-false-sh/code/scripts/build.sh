#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"

echo "=== Building Benchmark Suite ==="

# Check for clang-format availability (optional, for T041)
if command -v clang-format &> /dev/null; then
    echo "clang-format found: $(clang-format --version)"
else
    echo "Warning: clang-format not found. Skipping format check."
fi

# Compile verify_layout.cpp
echo "Compiling verify_layout.cpp..."
g++ -std=c++17 -O3 -march=native -Wall -Wextra \
    -o "$PROJECT_ROOT/bin/verify_layout" \
    "$BENCHMARK_DIR/verify_layout.cpp"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to compile verify_layout.cpp"
    exit 1
fi
echo "Successfully compiled verify_layout"

# Compile main.cpp
echo "Compiling main.cpp..."
g++ -std=c++17 -O3 -march=native -Wall -Wextra \
    -o "$PROJECT_ROOT/bin/benchmark_runner" \
    "$BENCHMARK_DIR/main.cpp"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to compile main.cpp"
    exit 1
fi
echo "Successfully compiled benchmark_runner"

# Create output directory
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/bin"

echo "=== Build Complete ==="
echo "Executables:"
echo "  - $PROJECT_ROOT/bin/verify_layout"
echo "  - $PROJECT_ROOT/bin/benchmark_runner"
