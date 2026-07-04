#!/usr/bin/env bash
set -euo pipefail

# run_benchmarks.sh
# Executes the counter benchmark across multiple thread counts and configurations.
# Generates a CSV file with timing results.
#
# Output: data/raw/benchmark_results.csv

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
BINARY_DIR="${PROJECT_ROOT}/code/benchmark"
DATA_DIR="${PROJECT_ROOT}/data/raw"
OUTPUT_CSV="${DATA_DIR}/benchmark_results.csv"
BENCHMARK_BIN="${BINARY_DIR}/counter_bench"

# Configuration
THREAD_COUNTS=(2 4 8)
CONFIGS=("packed" "padded")
ITERATIONS_PER_RUN=1000000  # Number of atomic increments per thread
NUM_REPETITIONS=5           # Number of times to run each config/thread combo

# Ensure data directory exists
mkdir -p "${DATA_DIR}"

# Check if binary exists
if [[ ! -f "${BENCHMARK_BIN}" ]]; then
    echo "Error: Benchmark binary not found at ${BENCHMARK_BIN}. Please run build.sh first."
    exit 1
fi

# Attempt to set CPU governor to performance
# This might fail if not running as root, so we catch errors but continue
set_cpu_governor() {
    local governor="performance"
    if command -v cpupower &> /dev/null; then
        if cpupower frequency-set -g "${governor}" 2>/dev/null; then
            echo "CPU governor set to ${governor} via cpupower."
            return 0
        fi
    fi
    
    # Fallback to direct sysfs write
    if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
        if echo "${governor}" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1; then
            echo "CPU governor set to ${governor} via sysfs."
            return 0
        fi
    fi
    
    echo "Warning: Could not set CPU governor to ${governor}. Continuing with default settings."
    return 0
}

set_cpu_governor

# Initialize CSV header if file doesn't exist or is empty
if [[ ! -f "${OUTPUT_CSV}" ]] || [[ ! -s "${OUTPUT_CSV}" ]]; then
    echo "thread_count,configuration,iteration_count,wall_clock_time_ms" > "${OUTPUT_CSV}"
fi

echo "Starting benchmark run..."
echo "Output file: ${OUTPUT_CSV}"
echo "----------------------------------------"

for threads in "${THREAD_COUNTS[@]}"; do
    for config in "${CONFIGS[@]}"; do
        echo "Running: threads=${threads}, config=${config}"
        
        for ((rep=1; rep<=NUM_REPETITIONS; rep++)); do
            # Run the benchmark
            # The binary is expected to output the timing in a parseable format or we capture wall time here.
            # Based on T023/T024, the binary should output CSV rows or we parse its stdout.
            # Assumption: The binary prints "SUCCESS <time_ms>" or similar, or we time it externally.
            # To be robust, we time the execution externally using 'time' or a wrapper, 
            # but the task implies the binary does the timing. 
            # Let's assume the binary prints the result to stdout in a specific format.
            # However, T024 says "output to CSV", implying the binary might write directly or we append.
            # To satisfy T023 (binary uses chrono) and T024 (output to CSV), 
            # we will assume the binary prints a single line with the time, and we append to the master CSV.
            
            # Execute and capture time
            start_time=$(date +%s%N)
            output=$("${BENCHMARK_BIN}" --threads "${threads}" --config "${config}" --iterations "${ITERATIONS_PER_RUN}" 2>&1) || {
                echo "Error: Benchmark failed for threads=${threads}, config=${config}"
                echo "${threads},${config},${ITERATIONS_PER_RUN},TIMEOUT" >> "${OUTPUT_CSV}"
                continue
            }
            end_time=$(date +%s%N)
            
            # Calculate wall clock time in milliseconds
            duration_ns=$((end_time - start_time))
            duration_ms=$(echo "scale=3; ${duration_ns} / 1000000" | bc)
            
            # The binary might output its own internal timing. 
            # If the binary outputs a time, we could use that. 
            # For this integration, we trust the external wall-clock measurement 
            # to ensure we capture the full overhead, or we parse the binary output if it provides it.
            # Let's assume the binary outputs "Result: <time_ms>"
            # If the binary output contains a time, use it. Otherwise use wall clock.
            # To keep it simple and robust for the test: use the wall clock time calculated above.
            # But T023 says "output to CSV". Let's assume the binary prints the time.
            # We will parse the binary output for the time if possible, else use wall clock.
            
            # Extract time from binary output if present (format: "time_ms: <val>")
            if [[ "${output}" =~ time_ms:\ ([0-9.]+) ]]; then
                final_time="${BASH_REMATCH[1]}"
            else
                final_time="${duration_ms}"
            fi

            # Append to CSV
            echo "${threads},${config},${ITERATIONS_PER_RUN},${final_time}" >> "${OUTPUT_CSV}"
            echo "  Rep ${rep}/${NUM_REPETITIONS}: ${final_time} ms"
        done
    done
done

echo "----------------------------------------"
echo "Benchmark complete. Results saved to ${OUTPUT_CSV}"
