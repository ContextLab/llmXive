#!/bin/bash
# build.sh - Compiles the benchmark harness and verification utilities
# Logs all output to build.log and exits with code 1 on compilation failure

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BENCHMARK_DIR="$PROJECT_ROOT/code/benchmark"
LOG_FILE="$PROJECT_ROOT/build.log"

# Clear previous log
: > "$LOG_FILE"

# Function to handle errors
handle_error() {
    echo "ERROR: Compilation failed" >> "$LOG_FILE"
    echo "ERROR: Compilation failed"
    exit 1
}

# Set trap to handle errors
trap handle_error ERR

echo "Starting build process..." | tee -a "$LOG_FILE"
echo "Compiler: g++" | tee -a "$LOG_FILE"
echo "Flags: -O3 -march=native" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"

# Compile verify_layout.cpp
echo "Compiling verify_layout.cpp..." | tee -a "$LOG_FILE"
g++ -O3 -march=native -std=c++17 \
    "$BENCHMARK_DIR/verify_layout.cpp" \
    -o "$BENCHMARK_DIR/verify_layout" \
    2>&1 | tee -a "$LOG_FILE"

# Compile main.cpp
echo "Compiling main.cpp..." | tee -a "$LOG_FILE"
g++ -O3 -march=native -std=c++17 \
    "$BENCHMARK_DIR/main.cpp" \
    -o "$BENCHMARK_DIR/benchmark" \
    2>&1 | tee -a "$LOG_FILE"

# Check for warnings in the log
if grep -qi "warning:" "$LOG_FILE" || grep -qi "warning" "$LOG_FILE"; then
    echo "WARNING: Compilation produced warnings. Check build.log for details." | tee -a "$LOG_FILE"
fi

# Verify binaries were created
if [[ ! -x "$BENCHMARK_DIR/verify_layout" ]]; then
    echo "ERROR: verify_layout binary not created or not executable" | tee -a "$LOG_FILE"
    handle_error
fi

if [[ ! -x "$BENCHMARK_DIR/benchmark" ]]; then
    echo "ERROR: benchmark binary not created or not executable" | tee -a "$LOG_FILE"
    handle_error
fi

echo "----------------------------------------" | tee -a "$LOG_FILE"
echo "Build completed successfully." | tee -a "$LOG_FILE"
echo "Binaries created:" | tee -a "$LOG_FILE"
echo "  - $BENCHMARK_DIR/verify_layout" | tee -a "$LOG_FILE"
echo "  - $BENCHMARK_DIR/benchmark" | tee -a "$LOG_FILE"

exit 0