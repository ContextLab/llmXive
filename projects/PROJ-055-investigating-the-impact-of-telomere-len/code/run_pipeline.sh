#!/bin/bash
#
# run_pipeline.sh
# Orchestration script for the Telomere-Lifespan Impact project.
#
# This script manages the execution order of pipeline stages, verifies
# input integrity via SHA256 checksums, and handles logging.
#
# Usage: ./run_pipeline.sh [stage]
# Stages: discover, ingest, clean, model, visualize, moderator, all
#

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CODE_DIR="$PROJECT_ROOT/code"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"
STATE_DIR="$PROJECT_ROOT/state/projects"
STATE_FILE="$STATE_DIR/PROJ-055-investigating-the-impact-of-telomere-len.yaml"

# Ensure directories exist
mkdir -p "$LOGS_DIR" "$DATA_DIR/raw" "$DATA_DIR/processed" "$DATA_DIR/phylogeny" "$STATE_DIR"

# --- Logging Setup ---
log_info() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [INFO] $1" | tee -a "$LOGS_DIR/pipeline.log"
}

log_error() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [ERROR] $1" | tee -a "$LOGS_DIR/pipeline.log" >&2
}

# --- Integrity Verification ---
verify_input_integrity() {
    local input_file="$1"
    local expected_hash="$2"
    
    if [[ ! -f "$input_file" ]]; then
        log_error "Input file not found: $input_file"
        return 1
    fi

    local current_hash=$(python3 -c "
import hashlib
import sys
path = sys.argv[1]
h = hashlib.sha256()
with open(path, 'rb') as f:
    for chunk in iter(lambda: f.read(8192), b''):
  h.update(chunk)
print(h.hexdigest())
" "$input_file")

    if [[ "$current_hash" != "$expected_hash" ]]; then
        log_error "Checksum mismatch for $input_file"
        log_error "  Expected: $expected_hash"
        log_error "  Found:    $current_hash"
        return 1
    fi
    
    log_info "Integrity verified for $input_file"
    return 0
}

# --- Stage Execution ---
run_stage() {
    local stage="$1"
    log_info "Starting stage: $stage"
    
    case "$stage" in
        discover)
            python3 "$CODE_DIR/01_discover_data.py"
            ;;
        ingest)
            python3 "$CODE_DIR/02_ingest_data.py"
            ;;
        clean)
            python3 "$CODE_DIR/03_clean_merge.py"
            ;;
        model)
            python3 "$CODE_DIR/04_model_pglS.py"
            ;;
        visualize)
            python3 "$CODE_DIR/05_visualize.py"
            ;;
        moderator)
            python3 "$CODE_DIR/06_moderator.py"
            ;;
        *)
            log_error "Unknown stage: $stage"
            exit 1
            ;;
    esac
    
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Stage $stage failed with exit code $exit_code"
        exit $exit_code
    fi
    
    log_info "Stage $stage completed successfully"
}

# --- Main Logic ---
main() {
    local stage="${1:-all}"
    
    log_info "Pipeline execution started for stage: $stage"
    
    if [[ "$stage" == "all" ]]; then
        local stages=("discover" "ingest" "clean" "model" "visualize" "moderator")
        for s in "${stages[@]}"; do
            run_stage "$s"
        done
    else
        run_stage "$stage"
    fi
    
    log_info "Pipeline execution finished"
}

main "$@"