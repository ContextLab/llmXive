#!/bin/bash
# run_pipeline.sh - Orchestrates the llmXive pipeline phases.
# Checks for HALT conditions from Phase 3 before running Phase 4/5.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_PROCESSED="$PROJECT_ROOT/data/processed"
VALIDATION_STATUS="$DATA_PROCESSED/validation_status.txt"

echo "=========================================="
echo "Starting llmXive Pipeline"
echo "=========================================="

# Phase 1 & 2 are assumed done or run via separate scripts if needed.
# We focus on the conditional execution of Phase 4 & 5.

# Check for HALT condition from Phase 3 (US1)
if [ -f "$VALIDATION_STATUS" ]; then
    STATUS=$(cat "$VALIDATION_STATUS" | tr -d '[:space:]')
    if [ "$STATUS" == "HALT" ]; then
        echo "⚠️  DATA BLOCKER DETECTED: $VALIDATION_STATUS contains 'HALT'."
        echo "Skipping Phase 4 (US2) and Phase 5 (US3) as per orchestration guard."
        exit 0
    fi
else
    # If status file doesn't exist, we assume Phase 3 hasn't run or passed without flagging.
    # However, for safety, if we are supposed to run Phase 4, we might need to ensure data exists.
    # For this script, we proceed if no explicit HALT is found.
    echo "No explicit HALT status found. Proceeding with Phase 4 check..."
fi

# Function to run a phase
run_phase() {
    local phase_name=$1
    local script=$2
    echo "Running $phase_name..."
    if [ -f "$script" ]; then
        python "$script"
        if [ $? -ne 0 ]; then
            echo "❌ $phase_name failed."
            exit 1
        fi
    else
        echo "⚠️  Script not found: $script"
    fi
}

# Phase 4: User Story 2 - Statistical Analysis
# Only run if US1 did not halt
if [ -f "$VALIDATION_STATUS" ]; then
    STATUS=$(cat "$VALIDATION_STATUS" | tr -d '[:space:]')
    if [ "$STATUS" != "HALT" ]; then
        run_phase "Phase 4 (US2)" "$PROJECT_ROOT/code/analysis/lmm_model.py"
        
        # Run correction and sensitivity if those scripts exist (T022, T023)
        # Assuming they are implemented in subsequent tasks
        if [ -f "$PROJECT_ROOT/code/analysis/correction.py" ]; then
            run_phase "Phase 4 (US2) Correction" "$PROJECT_ROOT/code/analysis/correction.py"
        fi
        if [ -f "$PROJECT_ROOT/code/analysis/sensitivity.py" ]; then
            run_phase "Phase 4 (US2) Sensitivity" "$PROJECT_ROOT/code/analysis/sensitivity.py"
        fi
    fi
else
    echo "⚠️  Validation status file missing. Skipping Phase 4 to ensure data integrity."
    exit 1
fi

# Phase 5: User Story 3 - Visualization and Reporting
# Only run if Phase 4 succeeded (implicit if we are here)
run_phase "Phase 5 (US3)" "$PROJECT_ROOT/code/reporting/visualize.py"
run_phase "Phase 5 (US3) Report" "$PROJECT_ROOT/code/reporting/generate_report.py"

echo "=========================================="
echo "Pipeline completed successfully."
echo "=========================================="
