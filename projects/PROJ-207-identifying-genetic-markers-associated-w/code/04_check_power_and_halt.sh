#!/bin/bash
#
# Task: T043
# Description: Execute power analysis (T005) immediately after data loading.
#              HALT the pipeline with ERR_SAMPLE_SIZE_INSUFFICIENT if n < 80
#              BEFORE any GWAS execution (T017) runs.
#
# This script enforces FR-012 halt logic early in the pipeline.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

POWER_ANALYSIS_SCRIPT="code/utils/power_analysis.py"
ERROR_CODE="ERR_SAMPLE_SIZE_INSUFFICIENT"

echo "----------------------------------------"
echo "Running Power Analysis Check (FR-012)..."
echo "----------------------------------------"

if [ ! -f "$POWER_ANALYSIS_SCRIPT" ]; then
    echo "ERROR: Power analysis script not found at $POWER_ANALYSIS_SCRIPT"
    exit 1
fi

# Execute the power analysis script.
# If n < 80, power_analysis.py will exit with code 1 and print the error code.
# We capture the output to check for the specific error message if needed,
# but the non-zero exit code is the primary signal to halt.
if ! python "$POWER_ANALYSIS_SCRIPT"; then
    EXIT_CODE=$?
    
    # Check if the exit code corresponds to the insufficient sample size error
    # The python script exits with 1 for ERR_SAMPLE_SIZE_INSUFFICIENT
    if [ $EXIT_CODE -ne 0 ]; then
        echo "----------------------------------------"
        echo "CRITICAL: Power analysis failed."
        echo "Pipeline HALTED due to insufficient sample size."
        echo "Error Code: $ERROR_CODE"
        echo "----------------------------------------"
        exit $EXIT_CODE
    fi
fi

echo "----------------------------------------"
echo "Power analysis passed. Sample size >= 80."
echo "Proceeding to GWAS execution (T017)..."
echo "----------------------------------------"

exit 0
