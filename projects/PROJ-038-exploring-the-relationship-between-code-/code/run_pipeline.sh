#!/bin/bash
#
# run_pipeline.sh - Orchestration script for the Code Complexity Bug Prediction Pipeline
#
# This script enforces the execution order:
# 1. Ingest (Download and filter Defects4J data)
# 2. Metrics (Calculate LOC, CC, Halstead)
# 3. Labeling (Assign is_buggy flags)
# 4. Analysis (Correlation and Modeling)
#
# Note: Analysis scripts are not yet implemented in this phase.
# The script will stop after Labeling with a clear status message.
#

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
LOG_FILE="$PROJECT_ROOT/pipeline.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    local level=$1
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $msg" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$*"; }
warn() { log "WARN" "$*"; }
error() { log "ERROR" "$*"; }

check_prerequisites() {
    info "Checking prerequisites..."

    # Check for Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        error "Python 3.11 not found. Please install python3.11."
        exit 1
    fi

    # Check for virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        warn "Virtual environment not found at $VENV_DIR. Creating it..."
        python3.11 -m venv "$VENV_DIR"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Check for required dependencies
    if ! python -c "import pandas" &> /dev/null; then
        error "Dependencies not installed. Please run 'pip install -r code/requirements.txt' first."
        exit 1
    fi

    # Check for Defects4J CLI (optional for this skeleton run, but good to warn)
    if ! command -v defects4j &> /dev/null; then
        warn "Defects4J CLI not found in PATH. Ensure it is installed and accessible."
    fi

    # Check for PMD (optional for this skeleton run)
    if ! command -v pmd &> /dev/null; then
        warn "PMD not found in PATH. Ensure it is installed and accessible."
    fi

    info "Prerequisites check passed."
}

run_ingest() {
    info "=== STEP 1: Ingest ==="
    info "Downloading and filtering Defects4J data..."
    
    if [ ! -f "code/src/ingest.py" ]; then
        error "Ingest script not found at code/src/ingest.py"
        exit 1
    fi

    # Run the ingest script
    # Note: This may take a while depending on the dataset size
    python code/src/ingest.py
    
    if [ $? -eq 0 ]; then
        info "Ingest completed successfully."
    else
        error "Ingest failed."
        exit 1
    fi
}

run_metrics() {
    info "=== STEP 2: Metrics ==="
    info "Calculating LOC, Cyclomatic Complexity, and Halstead Volume..."

    if [ ! -f "code/src/metrics.py" ]; then
        error "Metrics script not found at code/src/metrics.py"
        exit 1
    fi

    # Run the metrics script
    python code/src/metrics.py
    
    if [ $? -eq 0 ]; then
        info "Metrics calculation completed successfully."
    else
        error "Metrics calculation failed."
        exit 1
    fi
}

run_labeling() {
    info "=== STEP 3: Labeling ==="
    info "Assigning bug labels to features..."

    if [ ! -f "code/src/labeling.py" ]; then
        # Labeling is not yet implemented in this phase, but we check for the file
        warn "Labeling script not found at code/src/labeling.py. Skipping this step as per task T008 scope (Analysis not implemented)."
        return 0
    fi

    # Run the labeling script
    python code/src/labeling.py
    
    if [ $? -eq 0 ]; then
        info "Labeling completed successfully."
    else
        error "Labeling failed."
        exit 1
    fi
}

run_analysis() {
    info "=== STEP 4: Analysis ==="
    warn "Analysis scripts are not yet implemented in this phase (T008). Skipping correlation and modeling steps."
    warn "Once T021, T022, T023, etc. are complete, this step will run automatically."
}

main() {
    info "Starting Pipeline Execution..."
    check_prerequisites

    # Execute steps in order
    run_ingest
    run_metrics
    run_labeling
    
    # Analysis is skipped for now as per task description
    run_analysis

    info "=== Pipeline Execution Complete ==="
    info "Note: Analysis phase was skipped as it is not yet implemented."
    info "Check 'code/data/processed/features.csv' for intermediate results."
}

# Run main function
main "$@"