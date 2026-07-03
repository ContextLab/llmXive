#!/bin/bash
# run_ci_validation.sh
# CI script to execute the full workflow and validate runtime constraints (≤6h) and memory usage (≤7GB)
# Project: PROJ-209-quantifying-the-influence-of-topological
# Task: T035

set -e  # Exit on any error

# Configuration
MAX_RUNTIME_SECONDS=$((6 * 60 * 60))  # 6 hours in seconds
MAX_MEMORY_MB=$((7 * 1024))           # 7 GB in MB
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODE_DIR="$PROJECT_ROOT/code"
LOG_FILE="$PROJECT_ROOT/logs/ci_validation_$(date +%Y%m%d_%H%M%S).log"
START_TIME=$(date +%s)

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

echo "========================================"
echo "CI Validation Workflow Start"
echo "Project Root: $PROJECT_ROOT"
echo "Max Runtime: ${MAX_RUNTIME_SECONDS}s (6h)"
echo "Max Memory: ${MAX_MEMORY_MB}MB (7GB)"
echo "Log File: $LOG_FILE"
echo "========================================"

# Function to check memory usage
check_memory_usage() {
    local current_mem=$(ps -o rss= -p $$ 2>/dev/null || echo "0")
    # Convert to MB (rss is in KB)
    current_mem=$((current_mem / 1024))
    if [ "$current_mem" -gt "$MAX_MEMORY_MB" ]; then
        echo "[ERROR] Memory usage exceeded limit: ${current_mem}MB > ${MAX_MEMORY_MB}MB"
        return 1
    fi
    return 0
}

# Function to check runtime
check_runtime() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    if [ "$elapsed" -gt "$MAX_RUNTIME_SECONDS" ]; then
        echo "[ERROR] Runtime exceeded limit: ${elapsed}s > ${MAX_RUNTIME_SECONDS}s"
        return 1
    fi
    echo "[INFO] Elapsed time: ${elapsed}s / ${MAX_RUNTIME_SECONDS}s"
    return 0
}

# Function to run a Python script with monitoring
run_with_monitoring() {
    local script=$1
    local description=$2

    echo "[INFO] Starting: $description"
    check_runtime || return 1

    # Run the script
    cd "$CODE_DIR"
    if ! python "$script" 2>&1 | tee -a "$LOG_FILE"; then
        echo "[ERROR] Script $script failed"
        return 1
    fi

    check_memory_usage || return 1
    check_runtime || return 1

    echo "[INFO] Completed: $description"
    return 0
}

# Main workflow execution
echo "[INFO] Starting full workflow execution..."

# Step 1: Data Acquisition (T010-T017)
run_with_monitoring "01_data_acquisition.py" "Data Acquisition Phase" || exit 1

# Step 2: Data Processing (T018-T019)
run_with_monitoring "02_data_processing.py" "Data Processing Phase" || exit 1

# Step 3: Modeling (T020-T024)
run_with_monitoring "03_modeling.py" "Modeling Phase" || exit 1

# Step 4: Inference (T025-T029)
run_with_monitoring "04_inference.py" "Inference Phase" || exit 1

# Step 5: Validation (T030-T034)
run_with_monitoring "05_validation.py" "Validation Phase" || exit 1

# Final checks
echo "[INFO] Running final validation checks..."
check_runtime || exit 1
check_memory_usage || exit 1

# Verify output artifacts exist
REQUIRED_FILES=(
    "data/raw/pristine_structures.csv"
    "data/raw/defect_dataset_2022.csv"
    "data/processed/features.csv"
    "data/processed/targets.csv"
    "data/validation/Validation_Report.json"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$file" ]; then
        echo "[ERROR] Required output file missing: $file"
        exit 1
    fi
    echo "[INFO] Verified: $file"
done

# Calculate final runtime
END_TIME=$(date +%s)
TOTAL_ELAPSED=$((END_TIME - START_TIME))

echo "========================================"
echo "CI Validation Completed Successfully"
echo "Total Runtime: ${TOTAL_ELAPSED}s"
echo "Status: PASSED"
echo "========================================"

exit 0