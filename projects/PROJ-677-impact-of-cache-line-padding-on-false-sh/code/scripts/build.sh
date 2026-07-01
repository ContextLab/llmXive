#!/bin/bash
# Build script for the Cache Line Padding False Sharing Benchmark
# Compiles main.cpp and verify_layout.cpp with optimization flags
#
# Exit codes:
# 0 - Success
# 1 - Compilation failure or missing dependencies

set -e  # Exit immediately on error

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK_DIR="${PROJECT_ROOT}/benchmark"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"

# Source files
MAIN_CPP="${BENCHMARK_DIR}/main.cpp"
VERIFY_LAYOUT_CPP="${BENCHMARK_DIR}/verify_layout.cpp"
COUNTER_PACKED_HPP="${BENCHMARK_DIR}/counter_packed.hpp"
COUNTER_PADDED_HPP="${BENCHMARK_DIR}/counter_padded.hpp"

# Output binaries
BENCH_BIN="${BENCHMARK_DIR}/benchmark"
VERIFY_BIN="${BENCHMARK_DIR}/verify_layout"

# Compiler settings
CXX="${CXX:-g++}"
CXXFLAGS="-std=c++17 -O3 -march=native -Wall -Wextra -Werror"

echo "=== Cache Line Padding Benchmark Build System ==="
echo "Project Root: ${PROJECT_ROOT}"
echo "Compiler: ${CXX}"
echo "Flags: ${CXXFLAGS}"
echo ""

# Check for required source files
echo "Checking source files..."
if [[ ! -f "${MAIN_CPP}" ]]; then
    echo "ERROR: Missing main.cpp at ${MAIN_CPP}"
    exit 1
fi
if [[ ! -f "${VERIFY_LAYOUT_CPP}" ]]; then
    echo "ERROR: Missing verify_layout.cpp at ${VERIFY_LAYOUT_CPP}"
    exit 1
fi
if [[ ! -f "${COUNTER_PACKED_HPP}" ]]; then
    echo "ERROR: Missing counter_packed.hpp at ${COUNTER_PACKED_HPP}"
    exit 1
fi
if [[ ! -f "${COUNTER_PADDED_HPP}" ]]; then
    echo "ERROR: Missing counter_padded.hpp at ${COUNTER_PADDED_HPP}"
    exit 1
fi
echo "All source files found."
echo ""

# Check for compiler
if ! command -v ${CXX} &> /dev/null; then
    echo "ERROR: C++ compiler '${CXX}' not found. Please install g++ or set CXX environment variable."
    exit 1
fi
echo "Compiler found: ${CXX} --version"
${CXX} --version | head -n 1
echo ""

# Create output directory if it doesn't exist
mkdir -p "${BENCHMARK_DIR}"

# Compile main.cpp -> benchmark
echo "Compiling main.cpp -> benchmark..."
if ! ${CXX} ${CXXFLAGS} -o "${BENCH_BIN}" "${MAIN_CPP}"; then
    echo "ERROR: Failed to compile main.cpp"
    echo "Compilation warnings/errors above."
    exit 1
fi
echo "Successfully built: ${BENCH_BIN}"

# Compile verify_layout.cpp -> verify_layout
echo "Compiling verify_layout.cpp -> verify_layout..."
if ! ${CXX} ${CXXFLAGS} -o "${VERIFY_BIN}" "${VERIFY_LAYOUT_CPP}"; then
    echo "ERROR: Failed to compile verify_layout.cpp"
    echo "Compilation warnings/errors above."
    exit 1
fi
echo "Successfully built: ${VERIFY_BIN}"

echo ""
echo "=== Build Complete ==="
echo "Binaries generated:"
echo "  - ${BENCH_BIN}"
echo "  - ${VERIFY_BIN}"
echo ""
echo "Usage:"
echo "  Run layout verification: ${VERIFY_BIN}"
echo "  Run benchmark: ${BENCH_BIN} --threads <N> --config <packed|padded>"
echo ""
