#!/bin/bash
set -e

# ============================================================================
# Pipeline Orchestration Script
# Project: PROJ-038-exploring-the-relationship-between-code-
# Task: T008 - Skeleton orchestration for Ingest -> Metrics -> Labeling -> Analysis
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
PYTHON="python"
LOG_FILE="$PROJECT_ROOT/data/pipeline_execution.log"
EXIT_CODE=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

run_step() {
    local step_name="$1"
    local script_path="$2"
    
    log "${YELLOW}Starting step: $step_name${NC}"
    
    if [ ! -f "$script_path" ]; then
        log "${RED}Error: Script not found: $script_path${NC}"
        return 1
    fi

    # Execute the script
    if $PYTHON "$script_path" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}Completed step: $step_name${NC}"
        return 0
    else
        log "${RED}Failed step: $step_name${NC}"
        return 1
    fi
}

# Ensure directories exist
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/results"
mkdir -p "$PROJECT_ROOT/figures"

log "=========================================="
log "Starting Pipeline Execution"
log "=========================================="

# ---------------------------------------------------------------------------
# Step 1: Ingest
# ---------------------------------------------------------------------------
# Note: T004/T013 implementation required. This script calls the ingest module.
if run_step "Ingest (Defects4J Data Download)" "$PROJECT_ROOT/code/src/ingest.py"; then
    :
else
    log "${RED}Pipeline stopped at Ingest step.${NC}"
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Metrics
# ---------------------------------------------------------------------------
# Note: T014/T014b/T014c implementation required.
# This script is a placeholder to enforce execution order.
# In a full implementation, this would call a dedicated metrics extraction script.
log "${YELLOW}Starting step: Metrics Extraction${NC}"
if [ -f "$PROJECT_ROOT/code/src/metrics.py" ]; then
    if $PYTHON "$PROJECT_ROOT/code/src/metrics.py" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}Completed step: Metrics Extraction${NC}"
    else
        log "${RED}Failed step: Metrics Extraction${NC}"
        EXIT_CODE=1
    fi
else
    log "${YELLOW}Skipping Metrics Extraction: code/src/metrics.py not yet implemented (Expected in Phase 3)${NC}"
fi

# ---------------------------------------------------------------------------
# Step 3: Labeling
# ---------------------------------------------------------------------------
# Note: T015 implementation required.
log "${YELLOW}Starting step: Labeling (Bug Mapping)${NC}"
if [ -f "$PROJECT_ROOT/code/src/labeling.py" ]; then
    if $PYTHON "$PROJECT_ROOT/code/src/labeling.py" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}Completed step: Labeling (Bug Mapping)${NC}"
    else
        log "${RED}Failed step: Labeling (Bug Mapping)${NC}"
        EXIT_CODE=1
    fi
else
    log "${YELLOW}Skipping Labeling: code/src/labeling.py not yet implemented (Expected in Phase 3)${NC}"
fi

# ---------------------------------------------------------------------------
# Step 4: Analysis
# ---------------------------------------------------------------------------
# Note: T021+ implementation required.
# This step is explicitly noted as not yet implemented per task T008 description.
log "${YELLOW}Starting step: Analysis (Correlation & Modeling)${NC}"
if [ -f "$PROJECT_ROOT/code/src/analysis.py" ]; then
    if $PYTHON "$PROJECT_ROOT/code/src/analysis.py" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}Completed step: Analysis (Correlation & Modeling)${NC}"
    else
        log "${RED}Failed step: Analysis (Correlation & Modeling)${NC}"
        EXIT_CODE=1
    fi
else
    log "${YELLOW}Skipping Analysis: code/src/analysis.py not yet implemented (Expected in Phase 4)${NC}"
fi

# ---------------------------------------------------------------------------
# Step 5: Validation
# ---------------------------------------------------------------------------
# Runs the schema validator defined in T007
log "${YELLOW}Starting step: Schema Validation${NC}"
if [ -f "$PROJECT_ROOT/code/data/validate_schema.py" ]; then
    if $PYTHON "$PROJECT_ROOT/code/data/validate_schema.py" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}Completed step: Schema Validation${NC}"
    else
        log "${RED}Failed step: Schema Validation${NC}"
        EXIT_CODE=1
    fi
else
    log "${YELLOW}Skipping Validation: code/data/validate_schema.py not found${NC}"
fi

log "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    log "${GREEN}Pipeline Execution Finished Successfully${NC}"
else
    log "${RED}Pipeline Execution Finished with Errors${NC}"
fi
log "=========================================="

exit $EXIT_CODE