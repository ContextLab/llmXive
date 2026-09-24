#!/bin/bash
#
# run_benchmarks.sh - Execute multi-threaded counter benchmarks with CPU pinning
#
# This script configures the hardware environment (CPU governor and core pinning)
# before running the benchmark binary. It attempts to use `cpupower` first,
# falling back to direct sysfs writes if the tool is unavailable, as per
# Plan: Hardware Configuration Transparency.
#

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BINARY_PATH="${PROJECT_ROOT}/benchmark/benchmark_runner"
OUTPUT_DIR="${PROJECT_ROOT}/data/raw"
LOG_FILE="${PROJECT_ROOT}/state/logs/benchmark_run.log"

# Thread counts to test
THREAD_COUNTS=(2 4 8)
CONFIGS=("packed" "padded")

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"
mkdir -p "$(dirname "${LOG_FILE}")"

# Logging helper
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "${msg}" | tee -a "${LOG_FILE}"
}

# -----------------------------------------------------------------------------
# Hardware Configuration: CPU Governor and Pinning
# -----------------------------------------------------------------------------
configure_hardware() {
    log "Starting hardware configuration..."
    
    # 1. Set CPU Governor to 'performance'
    # Strategy: Try cpupower first, fallback to sysfs
    local governor_set=false
    
    if command -v cpupower &> /dev/null; then
        log "Attempting to set governor via cpupower..."
        if sudo cpupower frequency-set -g performance 2>/dev/null; then
            governor_set=true
            log "Success: Governor set to 'performance' via cpupower."
        else
            log "Warning: cpupower failed (likely permission denied). Attempting sysfs fallback..."
        fi
    else
        log "Warning: cpupower not found. Attempting sysfs fallback..."
    fi

    if [ "${governor_set}" = false ]; then
        # Fallback: Direct sysfs write
        # Iterate over all possible CPUs
        for cpu_dir in /sys/devices/system/cpu/cpu[0-9]*; do
            if [ -d "${cpu_dir}" ]; then
                local gov_file="${cpu_dir}/cpufreq/scaling_governor"
                if [ -w "${gov_file}" ]; then
                    if echo "performance" | sudo tee "${gov_file}" > /dev/null; then
                        log "Set ${cpu_dir} governor to 'performance' via sysfs."
                    else
                        log "Warning: Failed to set governor for ${cpu_dir} via sysfs."
                    fi
                fi
            fi
        done
    fi

    # Verify the setting (best effort)
    if [ -f "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" ]; then
        local current_gov=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
        if [ "${current_gov}" != "performance" ]; then
            log "Warning: Current governor is '${current_gov}', expected 'performance'. Benchmarks may be noisy."
        else
            log "Verified: Governor is 'performance'."
        fi
    fi

    # 2. Core Pinning (Affinity)
    # We will pin the benchmark process to specific cores based on thread count
    # using taskset. This is done per execution in the loop below.
    log "Hardware configuration complete."
}

# -----------------------------------------------------------------------------
# Benchmark Execution Loop
# -----------------------------------------------------------------------------
run_benchmarks() {
    if [ ! -x "${BINARY_PATH}" ]; then
        log "Error: Benchmark binary not found or not executable at ${BINARY_PATH}"
        log "Please run build.sh first."
        exit 1
    fi

    log "Starting benchmark execution..."

    for threads in "${THREAD_COUNTS[@]}"; do
        for config in "${CONFIGS[@]}"; do
            local output_file="${OUTPUT_DIR}/results_threads_${threads}_${config}.csv"
            
            log "Running: threads=${threads}, config=${config} -> ${output_file}"
            
            # Determine affinity mask for taskset
            # For simplicity, we pin to the first N cores available.
            # In a real high-precision scenario, we might reserve specific cores.
            # Here we use a mask of the first 'threads' cores (e.g., 2 threads -> 0x3)
            local mask=$(( (1 << threads) - 1 ))
            local mask_hex=$(printf "0x%x" ${mask})

            log "Pinning process to cores 0-${threads-1} (mask: ${mask_hex})"

            # Execute with taskset
            # We append to the file. The binary handles the CSV header if it's a new file.
            # We use timeout to prevent hanging indefinitely (e.g., 10 minutes per run)
            if timeout 600 sudo taskset -c 0-${threads-1} "${BINARY_PATH}" \
                --threads "${threads}" \
                --config "${config}" \
                --output "${output_file}" \
                2>&1 | tee -a "${LOG_FILE}"; then
                
                log "Success: Benchmark completed for threads=${threads}, config=${config}."
            else
                local exit_code=$?
                log "Warning: Benchmark failed or timed out for threads=${threads}, config=${config} (Exit code: ${exit_code})."
            fi
        done
    done

    log "All benchmark runs finished."
}

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
main() {
    log "=========================================="
    log "Starting Benchmark Suite (T025: CPU Pinning)"
    log "=========================================="
    
    configure_hardware
    run_benchmarks
    
    log "=========================================="
    log "Benchmark Suite Complete"
    log "=========================================="
}

main "$@"
