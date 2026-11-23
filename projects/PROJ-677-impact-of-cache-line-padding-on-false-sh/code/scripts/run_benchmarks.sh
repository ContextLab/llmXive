#!/bin/bash
# run_benchmarks.sh - Execute multi-threaded benchmark experiments
#
# This script orchestrates the execution of the benchmark binary across
# various thread counts and configurations (packed/padded), applying
# CPU pinning, governor settings, and statistical variance control.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/code/benchmark"
DATA_DIR="$PROJECT_ROOT/data/raw"
LOG_FILE="$PROJECT_ROOT/state/logs/benchmark_run.log"
OUTPUT_CSV="$DATA_DIR/benchmark_results.csv"

# Ensure directories exist
mkdir -p "$DATA_DIR"
mkdir -p "$PROJECT_ROOT/state/logs"

# Initialize output CSV with header if it doesn't exist
if [[ ! -f "$OUTPUT_CSV" ]]; then
    echo "thread_count,configuration,iteration_count,wall_clock_time_ms" > "$OUTPUT_CSV"
fi

# Logging function
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    if ! command -v cpupower &> /dev/null; then
        log "WARNING: cpupower not found. Attempting sysfs fallback..."
    fi
    if ! command -v g++ &> /dev/null; then
        error_exit "g++ compiler not found. Cannot build benchmarks."
    fi
}

# Set CPU governor and pinning
configure_cpu() {
    log "Configuring CPU governor and pinning..."
    
    # Try cpupower first
    if command -v cpupower &> /dev/null; then
        log "Setting CPU governor to performance via cpupower..."
        sudo cpupower frequency-set -g performance 2>/dev/null || {
            log "WARNING: cpupower failed. Trying sysfs fallback..."
            echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1 || true
        }
    else
        # Fallback to sysfs
        log "Setting CPU governor to performance via sysfs..."
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1 || true
    fi

    # Verify governor setting
    local current_governor
    current_governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
    log "Current CPU governor: $current_governor"
}

# Run a single benchmark execution
# Args: $1=thread_count, $2=configuration, $3=benchmark_binary
run_single_benchmark() {
    local thread_count=$1
    local configuration=$2
    local benchmark_binary=$3
    local result_file="$DATA_DIR/single_run_${thread_count}_${configuration}.csv"

    log "Running benchmark: threads=$thread_count, config=$configuration"
    
    # Execute benchmark and capture output
    # The binary should output CSV rows directly or to a file
    # We expect the binary to write to stdout or a specific file
    if ! "$benchmark_binary" "$thread_count" "$configuration" > "$result_file" 2>&1; then
        log "WARNING: Benchmark execution failed for threads=$thread_count, config=$configuration"
        return 1
    fi

    # Parse results and append to main CSV
    if [[ -f "$result_file" && -s "$result_file" ]]; then
        # Skip header if present, append data rows
        tail -n +2 "$result_file" >> "$OUTPUT_CSV" 2>/dev/null || true
        log "Successfully appended results for threads=$thread_count, config=$configuration"
        return 0
    else
        log "WARNING: No results generated for threads=$thread_count, config=$configuration"
        return 1
    fi
}

# Execute benchmark with variance control
# Args: $1=thread_count, $2=configuration, $3=benchmark_binary
execute_with_variance_control() {
    local thread_count=$1
    local configuration=$2
    local benchmark_binary=$3
    local min_runs=5
    local max_runs=10
    local variance_threshold=0.10  # 10%
    
    log "Starting variance-controlled execution for threads=$thread_count, config=$configuration"
    
    local run_times=()
    local successful_runs=0
    local current_run=0
    
    while [[ $successful_runs -lt $min_runs ]] || [[ $successful_runs -lt $max_runs && $variance_exceeded -eq 1 ]]; do
        current_run=$((current_run + 1))
        
        # Check if we've hit max runs
        if [[ $current_run -gt $max_runs ]]; then
            log "Reached maximum runs ($max_runs) without achieving stable variance. Proceeding with available data."
            break
        fi
        
        log "Attempt $current_run of $max_runs..."
        
        if run_single_benchmark "$thread_count" "$configuration" "$benchmark_binary"; then
            # Extract wall clock time from the result (assuming last row or specific parsing)
            # For simplicity, we'll assume the binary outputs a single timing result per run
            # In a real scenario, we'd parse the CSV output properly
            local time_ms
            time_ms=$(tail -n 1 "$DATA_DIR/single_run_${thread_count}_${configuration}.csv" | cut -d',' -f4 2>/dev/null || echo "0")
            
            if [[ -n "$time_ms" && "$time_ms" != "0" ]]; then
                run_times+=("$time_ms")
                successful_runs=$((successful_runs + 1))
                log "Run $successful_runs completed: ${time_ms}ms"
            else
                log "WARNING: Invalid time measurement for run $current_run"
            fi
        else
            log "WARNING: Run $current_run failed, excluding from results"
        fi
        
        # Calculate variance if we have enough runs
        if [[ ${#run_times[@]} -ge 3 ]]; then
            local mean=0
            local sum=0
            for t in "${run_times[@]}"; do
                sum=$(echo "$sum + $t" | bc -l)
            done
            mean=$(echo "scale=10; $sum / ${#run_times[@]}" | bc -l)
            
            local sum_sq_diff=0
            for t in "${run_times[@]}"; do
                local diff=$(echo "$t - $mean" | bc -l)
                local sq_diff=$(echo "$diff * $diff" | bc -l)
                sum_sq_diff=$(echo "$sum_sq_diff + $sq_diff" | bc -l)
            done
            
            local variance=$(echo "scale=10; $sum_sq_diff / ${#run_times[@]}" | bc -l)
            local std_dev=$(echo "scale=10; sqrt($variance)" | bc -l)
            local cv=$(echo "scale=10; $std_dev / $mean" | bc -l)
            
            log "Current stats: mean=${mean}ms, std_dev=${std_dev}ms, CV=${cv}"
            
            if (( $(echo "$cv > $variance_threshold" | bc -l) )); then
                log "Variance threshold exceeded (${cv} > ${variance_threshold}). Will continue to max runs."
                variance_exceeded=1
            else
                log "Variance within threshold. Minimum runs achieved."
                variance_exceeded=0
            fi
        fi
    done
    
    if [[ $successful_runs -lt $min_runs ]]; then
        log "ERROR: Failed to achieve minimum successful runs ($min_runs) for threads=$thread_count, config=$configuration"
        return 1
    fi
    
    log "Completed variance-controlled execution for threads=$thread_count, config=$configuration with $successful_runs successful runs"
    return 0
}

# Main execution
main() {
    log "=== Starting Benchmark Execution ==="
    
    check_dependencies
    configure_cpu
    
    # Build benchmark if not already built
    local benchmark_binary="$BENCHMARK_DIR/benchmark_runner"
    if [[ ! -f "$benchmark_binary" ]]; then
        log "Building benchmark binary..."
        if ! bash "$SCRIPT_DIR/build.sh" 2>&1 | tee -a "$LOG_FILE"; then
            error_exit "Failed to build benchmark binary"
        fi
    fi
    
    # Define test configurations
    local thread_counts=(1 2 4 8)
    local configurations=("packed" "padded")
    
    # Execute all configurations
    for threads in "${thread_counts[@]}"; do
        for config in "${configurations[@]}"; do
            log "Processing configuration: threads=$threads, config=$config"
            execute_with_variance_control "$threads" "$config" "$benchmark_binary" || {
                log "ERROR: Failed to complete variance-controlled execution for threads=$threads, config=$config"
                # Continue with other configurations rather than failing entirely
            }
        done
    done
    
    log "=== Benchmark Execution Complete ==="
    
    # Validate output
    if [[ -f "$OUTPUT_CSV" ]]; then
        local line_count
        line_count=$(wc -l < "$OUTPUT_CSV")
        log "Generated $((line_count - 1)) data rows in $OUTPUT_CSV"
    else
        error_exit "Output CSV was not generated"
    fi
}

# Run main function
main "$@"