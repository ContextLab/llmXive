#!/bin/bash
# Orchestration script for the Avian Foraging Behavior Prediction Pipeline
# This script runs all pipeline phases in the correct dependency order

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/pipeline_run.log"
echo "Pipeline started at $(date)" > "$LOG_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

run_step() {
    local step_name="$1"
    local script_path="$2"
    log "Starting step: $step_name"
    if [ -f "$script_path" ]; then
        python "$script_path" >> "$LOG_FILE" 2>&1
        log "Completed step: $step_name"
    else
        log "ERROR: Script not found: $script_path"
        exit 1
    fi
}

# Phase 1: Setup (if not already done)
log "=== Phase 1: Setup ==="
run_step "setup_directories" "${SCRIPT_DIR}/setup_directories.py"

# Phase 2: Foundational
log "=== Phase 2: Foundational ==="
# Note: config.py and provenance.py are imported by other scripts, 
# no standalone execution needed unless testing

# Phase 3: User Story 1 - Data Extraction and Merging
log "=== Phase 3: User Story 1 - Data Extraction ==="
run_step "download_ebd" "${SCRIPT_DIR}/data/download_ebd.py"
run_step "download_nlcd" "${SCRIPT_DIR}/data/download_nlcd.py"
run_step "generate_guild_mapping" "${SCRIPT_DIR}/data/generate_guild_mapping.py"
run_step "record_nlcd_provenance" "${SCRIPT_DIR}/data/record_nlcd_provenance.py"
run_step "select_top_species" "${SCRIPT_DIR}/data/select_top_species.py"
run_step "merge_and_buffer" "${SCRIPT_DIR}/data/merge_and_buffer.py"
run_step "aggregate" "${SCRIPT_DIR}/data/aggregate.py"
run_step "extract_top_species" "${SCRIPT_DIR}/data/extract_top_species.py"

# Phase 4: User Story 2 - Model Training and Evaluation
log "=== Phase 4: User Story 2 - Model Training ==="
run_step "train" "${SCRIPT_DIR}/models/train.py"
run_step "evaluate" "${SCRIPT_DIR}/models/evaluate.py"

# Phase 5: User Story 3 - Visualization
log "=== Phase 5: User Story 3 - Visualization ==="
run_step "plot_confusion" "${SCRIPT_DIR}/viz/plot_confusion.py"
run_step "plot_importance" "${SCRIPT_DIR}/viz/plot_importance.py"
run_step "map_habitat" "${SCRIPT_DIR}/viz/map_habitat.py"

log "=== Pipeline completed successfully ==="
log "Pipeline finished at $(date)"