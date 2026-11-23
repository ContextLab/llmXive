#!/bin/bash
# Security validation script for benchmark execution
# Ensures safe execution environment before running benchmarks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BENCH_DIR="$PROJECT_ROOT/code/benchmark"
BIN_DIR="$BENCH_DIR/bin"

# Validate paths
if [[ "$BENCH_DIR" != "$PROJECT_ROOT"* ]] || [[ "$BIN_DIR" != "$PROJECT_ROOT"* ]]; then
    echo "Error: Path traversal detected in script paths." >&2
    exit 1
fi

# Check for required binaries
if [[ ! -x "$BIN_DIR/benchmark_runner" ]] || [[ ! -x "$BIN_DIR/verify_layout" ]]; then
    echo "Error: Required binaries not found or not executable." >&2
    exit 1
fi

# Validate output directory permissions
OUTPUT_DIR="$PROJECT_ROOT/data/raw"
if [[ ! -d "$OUTPUT_DIR" ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

# Ensure output directory is not world-writable
if [[ $(stat -c %a "$OUTPUT_DIR") =~ [0-7][0-7][2367] ]]; then
    echo "Warning: Output directory is world-writable. Fixing permissions..."
    chmod 755 "$OUTPUT_DIR"
fi

echo "Environment validation passed. Safe to proceed with benchmark execution."