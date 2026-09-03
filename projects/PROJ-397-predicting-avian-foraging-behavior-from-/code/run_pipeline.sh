#!/bin/bash
# Automated Science Pipeline: Predicting Avian Foraging Behavior
# This script orchestrates the full data processing, modeling, and visualization pipeline.

set -e  # Exit immediately on error

echo "=========================================="
echo "Starting Avian Foraging Behavior Pipeline"
echo "=========================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/pipeline.log"

log_step() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

run_step() {
    local step_name="$1"
    local script_path="$2"
    log_step "Executing: $step_name"
    if python "$script_path"; then
        log_step "Success: $step_name"
    else
        log_step "FAILED: $step_name (exit code $?)"
        exit 1
    fi
}

# Phase 1: Data Download
log_step "=== Phase 1: Data Download ==="
run_step "Download EBD" "code/data/download_ebd.py"
run_step "Download NLCD" "code/data/download_nlcd.py"
run_step "Download Guild Source" "code/data/download_guild_source.py"

# Phase 2: Data Processing
log_step "=== Phase 2: Data Processing ==="
run_step "Generate Guild Mapping" "code/data/generate_guild_mapping.py"
run_step "Select Top Species" "code/data/select_top_species.py"
run_step "Merge and Buffer" "code/data/merge_and_buffer.py"
run_step "Aggregate Profiles" "code/data/aggregate.py"

# Phase 3: Model Training & Evaluation
log_step "=== Phase 3: Model Training & Evaluation ==="
run_step "Train Model" "code/models/train.py"
run_step "Evaluate Model" "code/models/evaluate.py"

# Phase 4: Visualization
log_step "=== Phase 4: Visualization ==="
run_step "Plot Confusion Matrix" "code/viz/plot_confusion.py"
run_step "Plot Feature Importance" "code/viz/plot_importance.py"
run_step "Map Habitat" "code/viz/map_habitat.py"

log_step "=========================================="
log_step "Pipeline completed successfully!"
log_step "=========================================="