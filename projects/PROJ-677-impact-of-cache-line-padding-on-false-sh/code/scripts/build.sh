#!/bin/bash

# build.sh
# Compiles the C++ benchmark harness.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="${PROJECT_ROOT}/benchmark"
OUTPUT_DIR="${PROJECT_ROOT}"
BINARY_NAME="benchmark_runner"

echo "Building benchmark harness..."

# Check for g++
if ! command -v g++ &> /dev/null; then
    echo "Error: g++ compiler not found." >&2
    exit 1
fi

# Compile main.cpp with optimizations
# -O3: High optimization
# -march=native: Optimize for current machine architecture
# -std=c++17: C++17 standard
# -pthread: Enable pthread support
g++ -O3 -march=native -std=c++17 -pthread \
    -o "${OUTPUT_DIR}/${BINARY_NAME}" \
    "${BENCHMARK_DIR}/main.cpp" \
    -I"${BENCHMARK_DIR}"

if [ $? -eq 0 ]; then
    echo "Build successful: ${OUTPUT_DIR}/${BINARY_NAME}"
else
    echo "Build failed." >&2
    exit 1
fi
