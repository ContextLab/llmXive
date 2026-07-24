#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")/../../.."
BENCHMARK_SCRIPT="$PROJECT_ROOT/code/scripts/run_benchmarks.sh"

echo "=== Integration Test: Benchmark Run ==="

# Check if build script exists
if [ ! -f "$BENCHMARK_SCRIPT" ]; then
    echo "Error: run_benchmarks.sh not found"
    exit 1
fi

# Check if binary exists
if [ ! -f "$PROJECT_ROOT/bin/benchmark_runner" ]; then
    echo "Error: benchmark_runner binary not found. Run build.sh first."
    exit 1
fi

# Run benchmarks
echo "Running benchmarks..."
bash "$BENCHMARK_SCRIPT"

# Check output file
OUTPUT_FILE="$PROJECT_ROOT/data/benchmark_results.csv"
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "Error: benchmark_results.csv not generated"
    exit 1
fi

# Check minimum number of lines (header + at least 5 samples per config * 2 configs * 3 thread counts)
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
EXPECTED_MIN=31  # 1 header + 30 data rows
if [ "$LINE_COUNT" -lt "$EXPECTED_MIN" ]; then
    echo "Error: Expected at least $EXPECTED_MIN lines, got $LINE_COUNT"
    exit 1
fi

echo "Integration test PASSED"
echo "Output file: $OUTPUT_FILE"
echo "Line count: $LINE_COUNT"
