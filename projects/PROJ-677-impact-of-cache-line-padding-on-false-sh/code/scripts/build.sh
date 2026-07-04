#!/usr/bin/env bash
set -euo pipefail

# build.sh
# Compiles the C++ benchmark binary with optimization flags.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
SRC_DIR="${PROJECT_ROOT}/code/benchmark"
BIN_DIR="${PROJECT_ROOT}/code/benchmark"

SRC_FILE="${SRC_DIR}/counter_bench.cpp"
OUTPUT_BIN="${BIN_DIR}/counter_bench"

echo "Building benchmark binary..."

if [[ ! -f "${SRC_FILE}" ]]; then
    echo "Error: Source file not found at ${SRC_FILE}"
    exit 1
fi

# Compile with C++17 and optimization flags
g++ -std=c++17 -O3 -march=native -pthread -o "${OUTPUT_BIN}" "${SRC_FILE}"

if [[ $? -eq 0 ]]; then
    echo "Build successful: ${OUTPUT_BIN}"
else
    echo "Build failed."
    exit 1
fi