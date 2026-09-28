#!/bin/bash
# build.sh - Compiles the C++ benchmark harness for cache line padding experiments
# Task: T017 - Add logging for compilation warnings/errors and exit with code 1 on failure

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCHMARK_DIR="${PROJECT_ROOT}/benchmark"
OUTPUT_DIR="${PROJECT_ROOT}/bin"
SRC_FILES=(
    "main.cpp"
    "verify_layout.cpp"
)
HEADER_FILES=(
    "counter_packed.hpp"
    "counter_padded.hpp"
)

# Compiler settings
CXX="${CXX:-g++}"
CXXFLAGS="-std=c++17 -O3 -march=native -Wall -Wextra -Wpedantic -Werror"

# Colors for logging
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

log "Starting build process..."
log "Compiler: ${CXX}"
log "Flags: ${CXXFLAGS}"
log "Source directory: ${BENCHMARK_DIR}"

# Check if all source files exist
for src in "${SRC_FILES[@]}"; do
    if [[ ! -f "${BENCHMARK_DIR}/${src}" ]]; then
        log_error "Source file not found: ${BENCHMARK_DIR}/${src}"
        exit 1
    fi
done

# Check if all header files exist
for hdr in "${HEADER_FILES[@]}"; do
    if [[ ! -f "${BENCHMARK_DIR}/${hdr}" ]]; then
        log_error "Header file not found: ${BENCHMARK_DIR}/${hdr}"
        exit 1
    fi
done

# Compile verify_layout executable
log "Compiling verify_layout..."
VERIFY_OUTPUT="${OUTPUT_DIR}/verify_layout"
if ! ${CXX} ${CXXFLAGS} -o "${VERIFY_OUTPUT}" "${BENCHMARK_DIR}/verify_layout.cpp" 2>&1; then
    log_error "Compilation of verify_layout failed. See errors above."
    exit 1
fi
log "verify_layout compiled successfully: ${VERIFY_OUTPUT}"

# Compile main benchmark executable
log "Compiling benchmark_main..."
BENCHMARK_OUTPUT="${OUTPUT_DIR}/benchmark_main"
if ! ${CXX} ${CXXFLAGS} -o "${BENCHMARK_OUTPUT}" "${BENCHMARK_DIR}/main.cpp" 2>&1; then
    log_error "Compilation of benchmark_main failed. See errors above."
    exit 1
fi
log "benchmark_main compiled successfully: ${BENCHMARK_OUTPUT}"

# Verify executables exist and are executable
if [[ ! -x "${VERIFY_OUTPUT}" ]]; then
    log_error "verify_layout executable not found or not executable"
    exit 1
fi

if [[ ! -x "${BENCHMARK_OUTPUT}" ]]; then
    log_error "benchmark_main executable not found or not executable"
    exit 1
fi

log "Build completed successfully!"
log "Executables available in: ${OUTPUT_DIR}"
log "  - verify_layout"
log "  - benchmark_main"

exit 0