#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../" && pwd )"
DATA_DIR="$PROJECT_ROOT/data"
CSV_FILE="$DATA_DIR/raw_benchmark_results.csv"

echo "Running integration test for benchmark run..."

# Ensure clean state
rm -f "$CSV_FILE"
mkdir -p "$DATA_DIR"

# Run the benchmark script
bash "$PROJECT_ROOT/code/scripts/run_benchmarks.sh"

# Check if file exists
if [ ! -f "$CSV_FILE" ]; then
    echo "FAIL: CSV file not generated."
    exit 1
fi

# Check if file has content (header + at least one row)
LINE_COUNT=$(wc -l < "$CSV_FILE")
if [ "$LINE_COUNT" -lt 2 ]; then
    echo "FAIL: CSV file is empty or has no data rows."
    exit 1
fi

# Check header
HEADER=$(head -n 1 "$CSV_FILE")
EXPECTED_HEADER="thread_count,configuration,iteration_count,wall_clock_time_ms"
if [ "$HEADER" != "$EXPECTED_HEADER" ]; then
    echo "FAIL: CSV header mismatch."
    echo "Expected: $EXPECTED_HEADER"
    echo "Got: $HEADER"
    exit 1
fi

# Check that we have samples for both configurations
PACKED_COUNT=$(grep -c ",packed," "$CSV_FILE" || true)
PADDED_COUNT=$(grep -c ",padded," "$CSV_FILE" || true)

if [ "$PACKED_COUNT" -eq 0 ]; then
    echo "FAIL: No 'packed' configuration samples found."
    exit 1
fi

if [ "$PADDED_COUNT" -eq 0 ]; then
    echo "FAIL: No 'padded' configuration samples found."
    exit 1
fi

echo "PASS: Benchmark run integration test successful."
echo "Generated $LINE_COUNT lines in $CSV_FILE"
echo "Packed samples: $PACKED_COUNT"
echo "Padded samples: $PADDED_COUNT"