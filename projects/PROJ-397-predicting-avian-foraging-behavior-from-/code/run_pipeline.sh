#!/bin/bash
# run_pipeline.sh - Orchestration script for the Avian Foraging Behavior Pipeline
# This script executes all pipeline stages in dependency order with error handling.

set -e  # Exit on first error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_DIR="${SCRIPT_DIR}"
LOG_FILE="${CODE_DIR}/pipeline_execution.log"

echo "=========================================="
echo "Starting Avian Foraging Behavior Pipeline"
echo "Started at: $(date)"
echo "=========================================="
echo ""

# Helper function to run a step
run_step() {
    local step_name="$1"
    local script_path="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Executing: ${step_name}"
    echo "  Script: ${script_path}"
    
    if python "${script_path}"; then
        echo "  Status: SUCCESS"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${step_name} completed successfully." >> "${LOG_FILE}"
    else
        echo "  Status: FAILED"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${step_name} failed with exit code $?." >> "${LOG_FILE}"
        echo "ERROR: Step '${step_name}' failed. Stopping pipeline."
        exit 1
    fi
    echo ""
}

# Phase 1: Data Download
echo ">>> PHASE 1: DATA DOWNLOAD"
run_step "Download eBird Data" "${CODE_DIR}/data/download_ebd.py"
run_step "Download NLCD Data" "${CODE_DIR}/data/download_nlcd.py"
run_step "Download Guild Source" "${CODE_DIR}/data/download_guild_source.py"
run_step "Generate Guild Mapping" "${CODE_DIR}/data/generate_guild_mapping.py"

# Phase 2: Data Preprocessing
echo ">>> PHASE 2: DATA PREPROCESSING"
run_step "Load and Count Species" "${CODE_DIR}/data/load_and_count.py"
run_step "Select Top Species" "${CODE_DIR}/data/select_top_species.py"
run_step "Preprocess Data" "${CODE_DIR}/data/preprocess.py"
run_step "Merge and Buffer" "${CODE_DIR}/data/merge_and_buffer.py"
run_step "Aggregate Species Profiles" "${CODE_DIR}/data/aggregate.py"

# Phase 3: Model Training
echo ">>> PHASE 3: MODEL TRAINING"
run_step "Train Random Forest" "${CODE_DIR}/models/train.py"

# Phase 4: Model Evaluation
echo ">>> PHASE 4: MODEL EVALUATION"
run_step "Evaluate Model" "${CODE_DIR}/models/evaluate.py"

# Phase 5: Visualization
echo ">>> PHASE 5: VISUALIZATION"
run_step "Plot Confusion Matrix" "${CODE_DIR}/viz/plot_confusion.py"
run_step "Plot Feature Importance" "${CODE_DIR}/viz/plot_importance.py"
run_step "Map Habitat" "${CODE_DIR}/viz/map_habitat.py"

echo "=========================================="
echo "Pipeline completed successfully!"
echo "Finished at: $(date)"
echo "=========================================="