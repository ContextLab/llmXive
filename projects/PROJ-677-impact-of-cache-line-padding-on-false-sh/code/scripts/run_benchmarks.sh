#!/bin/bash
# run_benchmarks.sh - Execute multi-threaded benchmarks with timeout handling
#
# This script iterates over thread counts {2, 4, 8} and configurations {packed, padded},
# runs the benchmark binary, and collects timing data into a CSV file.
# It implements timeout handling to flag incomplete runs.

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/code/benchmark"
DATA_DIR="$PROJECT_ROOT/data/raw"
BINARY="counter_benchmark"
CSV_OUTPUT="$DATA_DIR/benchmark_results.csv"
ITERATIONS=10000000  # 10M increments per thread
TIMEOUT_SECONDS=300 # 5 minutes per run
REPEATS=5           # Number of repetitions per config

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Initialize CSV header if file doesn't exist
if [ ! -f "$CSV_OUTPUT" ]; then
    echo "thread_count,configuration,iteration_count,wall_clock_time_ms,status" > "$CSV_OUTPUT"
fi

# Setup CPU governor (from T025)
setup_cpu_governor() {
    if command -v cpupower &> /dev/null; then
        sudo cpupower frequency-set -g performance 2>/dev/null || true
    else
        # Fallback to direct sysfs write
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            if [ -w "$cpu" ]; then
                echo performance | sudo tee "$cpu" >/dev/null 2>&1 || true
            fi
        done
    fi
}

# Run a single benchmark configuration
run_benchmark() {
    local thread_count=$1
    local config=$2
    local iteration_count=$3
    local timeout=$4
    
    echo "Running: threads=$thread_count, config=$config, iters=$iteration_count"
    
    # Run with timeout and capture output
    local output
    local exit_code
    
    output=$(timeout --signal=KILL "${timeout}s" \
        "$BENCHMARK_DIR/$BINARY" \
        --threads "$thread_count" \
        --config "$config" \
        --iterations "$iteration_count" \
        2>&1) || exit_code=$?
    
    # Check for timeout (exit code 137 = killed by signal 9, or 124 from timeout command)
    if [ "${exit_code:-0}" -eq 124 ] || [ "${exit_code:-0}" -eq 137 ]; then
        echo "  TIMEOUT: Run exceeded ${timeout}s limit"
        echo "${thread_count},${config},${iteration_count},0,TIMEOUT" >> "$CSV_OUTPUT"
        return 1
    fi
    
    # Parse timing from output (expected format: "Wall clock time: X.XX ms")
    local wall_time_ms
    wall_time_ms=$(echo "$output" | grep "Wall clock time:" | awk '{print $4}')
    
    if [ -z "$wall_time_ms" ]; then
        echo "  WARNING: Could not parse timing from output"
        echo "${thread_count},${config},${iteration_count},0,ERROR" >> "$CSV_OUTPUT"
        return 1
    fi
    
    echo "  Result: ${wall_time_ms} ms"
    echo "${thread_count},${config},${iteration_count},${wall_time_ms},OK" >> "$CSV_OUTPUT"
    return 0
}

# Main execution
echo "Starting benchmark suite..."
echo "Binary: $BENCHMARK_DIR/$BINARY"
echo "Output: $CSV_OUTPUT"
echo "Timeout per run: ${TIMEOUT_SECONDS}s"
echo "Iterations per thread: $ITERATIONS"
echo ""

# Setup environment
setup_cpu_governor

# Check if binary exists
if [ ! -f "$BENCHMARK_DIR/$BINARY" ]; then
    echo "ERROR: Benchmark binary not found at $BENCHMARK_DIR/$BINARY"
    echo "Please run build.sh first."
    exit 1
fi

# Run experiments
for threads in 2 4 8; do
    for config in packed padded; do
        echo "=== Thread Count: $threads, Config: $config ==="
        
        for ((i=1; i<=REPEATS; i++)); do
            echo "  Repetition $i/$REPEATS"
            run_benchmark "$threads" "$config" "$ITERATIONS" "$TIMEOUT_SECONDS" || true
            # Small delay between runs to ensure statistical independence
            sleep 1
        done
        echo ""
    done
done

echo "Benchmark suite completed."
echo "Results written to: $CSV_OUTPUT"

# Count timeout vs successful runs
local total_runs
local timeout_runs
local success_runs

total_runs=$(tail -n +2 "$CSV_OUTPUT" | wc -l)
timeout_runs=$(grep ",TIMEOUT$" "$CSV_OUTPUT" | wc -l)
success_runs=$(grep ",OK$" "$CSV_OUTPUT" | wc -l)

echo ""
echo "Summary:"
echo "  Total runs: $total_runs"
echo "  Successful: $success_runs"
echo "  Timeouts: $timeout_runs"

if [ "$timeout_runs" -gt 0 ]; then
    echo "  WARNING: Some runs timed out and were flagged. These will be excluded from analysis."
fi

exit 0
