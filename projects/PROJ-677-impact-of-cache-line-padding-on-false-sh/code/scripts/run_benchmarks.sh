#!/bin/bash
# run_benchmarks.sh - Execute the cache line padding benchmark
# Handles core pinning via taskset and output directory creation
#
# Usage: ./run_benchmarks.sh [output_dir]
#
# Environment variables:
#   BENCHMARK_THREADS: Thread counts to test (default: 2 4 8)
#   BENCHMARK_CONFIGS: Configurations to test (default: packed padded)
#   BENCHMARK_RUNS: Number of repetitions per config (default: 5)
#   BENCHMARK_OUTPUT_DIR: Output directory (default: data/raw)

set -euo pipefail

# Configuration
THREAD_COUNTS="${BENCHMARK_THREADS:-2 4 8}"
CONFIGS="${BENCHMARK_CONFIGS:-packed padded}"
NUM_RUNS="${BENCHMARK_RUNS:-5}"
OUTPUT_DIR="${BENCHMARK_OUTPUT_DIR:-data/raw}"
BINARY_PATH="code/benchmark/benchmark"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure we are in the project root
cd "$PROJECT_ROOT"

# Create output directory
echo "Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Check if benchmark binary exists
if [[ ! -x "$BINARY_PATH" ]]; then
    echo "ERROR: Benchmark binary not found or not executable: $BINARY_PATH"
    echo "Please run ./build.sh first."
    exit 1
fi

# Function to set CPU governor to performance
set_cpu_governor() {
    echo "Setting CPU governor to 'performance'..."
    if command -v cpupower &> /dev/null; then
        sudo cpupower frequency-set -g performance
    else
        # Fallback to direct sysfs write
        for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            if [[ -w "$cpu" ]]; then
                echo "performance" | sudo tee "$cpu" > /dev/null
            fi
        done
    fi
    echo "CPU governor set."
}

# Function to pin process to specific cores
pin_to_cores() {
    local core_range="$1"
    echo "Pinning to cores: $core_range"
}

# Set CPU governor
set_cpu_governor

# Initialize CSV header
CSV_FILE="$OUTPUT_DIR/benchmark_results.csv"
echo "thread_count,configuration,iteration_count,wall_clock_time_ms,core_pinning,status" > "$CSV_FILE"

# Get total available cores
TOTAL_CORES=$(nproc)
echo "Total available cores: $TOTAL_CORES"

# Run benchmarks
for threads in $THREAD_COUNTS; do
    for config in $CONFIGS; do
        echo "========================================"
        echo "Running: threads=$threads, config=$config"
        echo "========================================"

        for run in $(seq 1 $NUM_RUNS); do
            echo "  Run $run/$NUM_RUNS..."

            # Determine core range for this thread count
            # Simple strategy: pin to first $threads cores
            if [[ $threads -le $TOTAL_CORES ]]; then
                CORE_RANGE=$(seq -s, 0 $((threads - 1)))
            else
                CORE_RANGE=$(seq -s, 0 $((TOTAL_CORES - 1)))
                echo "  WARNING: Requested threads ($threads) > available cores ($TOTAL_CORES). Using all cores."
            fi

            # Prepare taskset command
            TASKSET_CMD="taskset -c $CORE_RANGE"

            # Run benchmark with timeout (30 seconds per run)
            START_TIME=$(date +%s%N)
            
            if timeout 30s $TASKSET_CMD $BINARY_PATH --threads $threads --config $config >> "$CSV_FILE" 2>&1; then
                END_TIME=$(date +%s%N)
                ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))
                echo "  Completed in ${ELAPSED_MS}ms"
            else
                echo "  TIMEOUT or ERROR"
                # Append timeout row
                echo "$threads,$config,0,0,$CORE_RANGE,TIMEOUT" >> "$CSV_FILE"
            fi
        done
    done
done

echo "========================================"
echo "Benchmark complete."
echo "Results written to: $CSV_FILE"
echo "========================================"

# Reset CPU governor to default (optional)
# echo "Resetting CPU governor to default..."
# if command -v cpupower &> /dev/null; then
#     sudo cpupower frequency-set -g schedutil
# fi
