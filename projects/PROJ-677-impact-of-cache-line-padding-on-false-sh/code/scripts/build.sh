#!/bin/bash
# build.sh - Compiles the cache line padding benchmark harness
#
# This script compiles main.cpp and verify_layout.cpp with optimization flags.
# It implements robust logging for compilation warnings/errors and exits with
# code 1 on any failure, ensuring the build process is transparent and fails loudly.

set -e  # Exit immediately on any command failure

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"
BUILD_DIR="$PROJECT_ROOT/build"

# Source files
MAIN_CPP="$BENCHMARK_DIR/main.cpp"
VERIFY_LAYOUT_CPP="$BENCHMARK_DIR/verify_layout.cpp"

# Compiler settings
CXX="${CXX:-g++}"
CXXFLAGS="-O3 -march=native -Wall -Wextra -Werror"

# Output binaries
BENCHMARK_BIN="$BUILD_DIR/benchmark"
VERIFY_BIN="$BUILD_DIR/verify_layout"

# Logging helper
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log_info() {
    log "INFO: $1"
}

log_warn() {
    log "WARN: $1" >&2
}

log_error() {
    log "ERROR: $1" >&2
}

# Ensure build directory exists
log_info "Creating build directory: $BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Check for required source files
if [[ ! -f "$MAIN_CPP" ]]; then
    log_error "Source file not found: $MAIN_CPP"
    exit 1
fi

if [[ ! -f "$VERIFY_LAYOUT_CPP" ]]; then
    log_error "Source file not found: $VERIFY_LAYOUT_CPP"
    exit 1
fi

# Compile verify_layout.cpp
log_info "Compiling verify_layout.cpp..."
if ! $CXX $CXXFLAGS -o "$VERIFY_BIN" "$VERIFY_LAYOUT_CPP" 2>&1; then
    log_error "Compilation of verify_layout.cpp failed."
    exit 1
fi
log_info "Successfully compiled: $VERIFY_BIN"

# Compile main.cpp
log_info "Compiling main.cpp..."
if ! $CXX $CXXFLAGS -o "$BENCHMARK_BIN" "$MAIN_CPP" 2>&1; then
    log_error "Compilation of main.cpp failed."
    exit 1
fi
log_info "Successfully compiled: $BENCHMARK_BIN"

log_info "Build completed successfully."
log_info "Binaries available in: $BUILD_DIR"
echo "  - $BENCHMARK_BIN"
echo "  - $VERIFY_BIN"

# Verify binaries exist and are executable
if [[ ! -x "$BENCHMARK_BIN" ]] || [[ ! -x "$VERIFY_BIN" ]]; then
    log_error "One or more binaries are not executable."
    exit 1
fi

exit 0