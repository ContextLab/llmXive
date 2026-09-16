#!/bin/bash
# Security-hardened build script for PROJ-677
# Implements: Input validation, restricted execution, safe compilation flags

set -euo pipefail

# --- Security Hardening: Input Validation ---
# Prevent command injection and path traversal
if [[ $# -ne 0 ]]; then
    echo "Error: build.sh does not accept arguments." >&2
    echo "Usage: ./build.sh" >&2
    exit 1
fi

# Define strict working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BENCH_DIR="$PROJECT_ROOT/code/benchmark"

# Validate paths are within project root (prevent path traversal)
if [[ "$BENCH_DIR" != "$PROJECT_ROOT"* ]]; then
    echo "Error: Benchmark directory is outside project root." >&2
    exit 1
fi

# --- Security Hardening: Environment ---
# Disable shell globbing expansion for safety
set -f
# Unset dangerous environment variables
unset LD_PRELOAD LD_LIBRARY_PATH LD_AUDIT

# --- Security Hardening: Compilation Flags ---
# Use safe C++17 standard
CXX="g++"
CXXFLAGS="-std=c++17 -Wall -Wextra -Werror -Wformat=2 -Wformat-security"

# Security hardening flags (if supported by compiler)
# -D_FORTIFY_SOURCE=2: Runtime buffer overflow detection
# -fstack-protector-strong: Stack smashing protection
# -Wl,-z,relro,-z,now: Full RELRO (relocation read-only)
# -fPIE -pie: Position Independent Executable
HARDENING_FLAGS="-D_FORTIFY_SOURCE=2 -fstack-protector-strong -Wl,-z,relro,-z,now -fPIE -pie"

# --- Security Hardening: Source Verification ---
# Check that source files exist and are not empty
REQUIRED_SOURCES=("main.cpp" "verify_layout.cpp" "counter_packed.hpp" "counter_padded.hpp")
for src in "${REQUIRED_SOURCES[@]}"; do
    if [[ ! -f "$BENCH_DIR/$src" ]]; then
        echo "Error: Required source file missing: $BENCH_DIR/$src" >&2
        exit 1
    fi
    if [[ ! -s "$BENCH_DIR/$src" ]]; then
        echo "Error: Source file is empty: $BENCH_DIR/$src" >&2
        exit 1
    fi
done

# --- Security Hardening: Build Execution ---
# Create output directory securely
OUTPUT_DIR="$PROJECT_ROOT/code/benchmark/bin"
mkdir -p "$OUTPUT_DIR"

# Compile verify_layout
echo "Compiling verify_layout..."
"$CXX" $CXXFLAGS $HARDENING_FLAGS -O3 -march=native \
    "$BENCH_DIR/verify_layout.cpp" \
    -o "$OUTPUT_DIR/verify_layout"

if [[ ! -x "$OUTPUT_DIR/verify_layout" ]]; then
    echo "Error: verify_layout compilation failed or output not executable." >&2
    exit 1
fi

# Compile main benchmark
echo "Compiling benchmark harness..."
"$CXX" $CXXFLAGS $HARDENING_FLAGS -O3 -march=native \
    "$BENCH_DIR/main.cpp" \
    -o "$OUTPUT_DIR/benchmark_runner"

if [[ ! -x "$OUTPUT_DIR/benchmark_runner" ]]; then
    echo "Error: benchmark_runner compilation failed or output not executable." >&2
    exit 1
fi

# Set strict permissions on binaries (owner read/write/execute only)
chmod 700 "$OUTPUT_DIR/verify_layout"
chmod 700 "$OUTPUT_DIR/benchmark_runner"

echo "Build completed successfully with security hardening flags."
echo "Binaries available in: $OUTPUT_DIR"
