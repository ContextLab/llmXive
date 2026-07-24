#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_BIN="$PROJECT_ROOT/bin/benchmark_runner"
OUTPUT_FILE="$PROJECT_ROOT/data/benchmark_results.csv"

# Check if binary exists
if [ ! -f "$BENCHMARK_BIN" ]; then
    echo "Error: Benchmark binary not found at $BENCHMARK_BIN"
    echo "Run build.sh first."
    exit 1
fi

# Clear previous results
rm -f "$OUTPUT_FILE"
echo "thread_count,configuration,iteration_count,wall_clock_time_ms" > "$OUTPUT_FILE"

# Configuration
THREAD_COUNTS=(2 4 8)
CONFIGS=("packed" "padded")
ITERATIONS=1000000
REPEATS=5

echo "=== Running Benchmarks ==="
echo "Thread counts: ${THREAD_COUNTS[*]}"
echo "Configs: ${CONFIGS[*]}"
echo "Iterations per thread: $ITERATIONS"
echo "Repeats per config: $REPEATS"
echo ""

for threads in "${THREAD_COUNTS[@]}"; do
    for config in "${CONFIGS[@]}"; do
        echo "Running: threads=$threads, config=$config"
        
        for ((i=1; i<=REPEATS; i++)); do
            echo "  Run $i/$REPEATS..."
            "$BENCHMARK_BIN" "$threads" "$config" "$ITERATIONS" >> "$OUTPUT_FILE"
        done
        echo ""
    done
done

echo "=== Benchmarks Complete ==="
echo "Results written to: $OUTPUT_FILE"
echo "Sample output:"
head -n 10 "$OUTPUT_FILE"
