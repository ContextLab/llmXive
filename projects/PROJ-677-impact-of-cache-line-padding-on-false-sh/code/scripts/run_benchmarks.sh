#!/bin/bash
# run_benchmarks.sh - Orchestrates the benchmark execution with environment configuration
# Handles core pinning via taskset and output directory creation
# Dependencies: taskset, cpupower (optional), mkdir, date
# Project: PROJ-677-impact-of-cache-line-padding-false-sh

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BENCHMARK_DIR="${PROJECT_ROOT}/code/benchmark"
DATA_DIR="${PROJECT_ROOT}/data/raw"
LOG_DIR="${PROJECT_ROOT}/state/logs"
BINARY_NAME="counter_benchmark"
BINARY_PATH="${BENCHMARK_DIR}/${BINARY_NAME}"

# Experiment parameters
THREAD_COUNTS=(2 4 8)
CONFIGS=("packed" "padded")
ITERATIONS_PER_RUN=5
INCREMENTS_PER_THREAD=10000000  # 10M increments per thread
TIMEOUT_SECONDS=300

# --- Helper Functions ---

log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

ensure_directories() {
    log_info "Creating output directories..."
    mkdir -p "${DATA_DIR}"
    mkdir -p "${LOG_DIR}"
    if [ ! -d "${BENCHMARK_DIR}" ]; then
        log_error "Benchmark directory not found: ${BENCHMARK_DIR}"
        exit 1
    fi
}

check_binary() {
    if [ ! -f "${BINARY_PATH}" ]; then
        log_error "Benchmark binary not found: ${BINARY_PATH}"
        log_error "Please run build.sh first."
        exit 1
    fi
    if [ ! -x "${BINARY_PATH}" ]; then
        log_error "Benchmark binary is not executable."
        exit 1
    fi
}

set_cpu_governor() {
    log_info "Setting CPU governor to 'performance'..."
    if command -v cpupower &> /dev/null; then
        sudo cpupower frequency-set -g performance 2>/dev/null || true
    else
        # Fallback to direct sysfs write if cpupower is not available
        # Requires root privileges
        for file in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
            if [ -w "$file" ]; then
                echo performance | sudo tee "$file" > /dev/null || true
            fi
        done
    fi
}

run_benchmark_run() {
    local thread_count=$1
    local config=$2
    local run_index=$3
    local output_file="${DATA_DIR}/benchmark_${thread_count}t_${config}_run${run_index}.csv"
    local log_file="${LOG_DIR}/benchmark_${thread_count}t_${config}_run${run_index}.log"
    
    log_info "Running: Threads=${thread_count}, Config=${config}, Run=${run_index}"
    
    # Determine taskset affinity mask
    # We pin the process to the first 'thread_count' logical cores
    # Example: if thread_count=2, mask=0x3 (binary 11) -> cores 0,1
    local mask=$(printf '0x%x' $(( (1 << thread_count) - 1 )))
    
    # Construct command
    # taskset -c specifies specific CPUs. We use 0 to (thread_count-1)
    local affinity_args=""
    for (( i=0; i<thread_count; i++ )); do
        if [ -z "$affinity_args" ]; then
            affinity_args="-c $i"
        else
            affinity_args="$affinity_args,$i"
        fi
    done

    # Run the benchmark
    # Arguments: thread_count, config, increments_per_thread
    # Output is redirected to the CSV file
    if timeout "${TIMEOUT_SECONDS}" taskset ${affinity_args} "${BINARY_PATH}" "${thread_count}" "${config}" "${INCREMENTS_PER_THREAD}" > "${output_file}" 2>> "${log_file}"; then
        log_info "Completed: ${output_file}"
    else
        local exit_code=$?
        log_error "Run failed with exit code ${exit_code}. Check ${log_file} for details."
        # Append a status line indicating failure if the file exists but is empty or partial
        if [ -f "${output_file}" ]; then
            echo "thread_count,configuration,iteration_count,wall_clock_time_ms,status" > "${output_file}"
            echo "${thread_count},${config},${INCREMENTS_PER_THREAD},0,TIMEOUT" >> "${output_file}"
        fi
    fi
}

# --- Main Execution ---

main() {
    log_info "Starting benchmark orchestration..."
    
    ensure_directories
    check_binary
    set_cpu_governor

    log_info "Starting experiment with thread counts: ${THREAD_COUNTS[*]}"
    log_info "Configs: ${CONFIGS[*]}"
    log_info "Iterations per config: ${ITERATIONS_PER_RUN}"

    for thread_count in "${THREAD_COUNTS[@]}"; do
        for config in "${CONFIGS[@]}"; do
            for (( run=1; run<=ITERATIONS_PER_RUN; run++ )); do
                run_benchmark_run "${thread_count}" "${config}" "${run}"
            done
        done
    done

    log_info "All benchmark runs completed."
    log_info "Results saved in ${DATA_DIR}"
}

# Only run main if this script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
