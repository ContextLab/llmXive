#!/bin/bash
#
# code/04_check_power_and_halt.sh
#
# Implements FR-012: Enforce minimum sample size (n >= 80) before GWAS execution.
# This script runs immediately after data loading and halts the pipeline if
# the sample size is insufficient.
#
# Exit Codes:
#   0 - Power analysis passed, pipeline can proceed
#   1 - Power analysis failed (sample size insufficient) or other error
#

set -e

# Define the path to the power analysis utility
POWER_ANALYSIS_SCRIPT="code/utils/power_analysis.py"

# Define the error code for insufficient sample size
ERR_CODE="ERR_SAMPLE_SIZE_INSUFFICIENT"

echo "=========================================="
echo "Starting Power Analysis Check (FR-012)"
echo "=========================================="

# Check if the power analysis script exists
if [ ! -f "$POWER_ANALYSIS_SCRIPT" ]; then
    echo "ERROR: Power analysis script not found at $POWER_ANALYSIS_SCRIPT"
    echo "HALTING pipeline."
    exit 1
fi

# Execute the power analysis
# The Python script will:
# 1. Locate input data (phenotypes/fam file)
# 2. Count samples (n)
# 3. If n < 80: Print error and exit with code 1
# 4. If n >= 80: Calculate power, write report, exit with code 0
python "$POWER_ANALYSIS_SCRIPT"
POWER_EXIT_CODE=$?

if [ $POWER_EXIT_CODE -ne 0 ]; then
    echo "=========================================="
    echo "PIPELINE HALTED: Insufficient Sample Size"
    echo "=========================================="
    echo "The power analysis failed. This likely means the sample size (n) is less than 80."
    echo "Error code: $ERR_CODE"
    echo "Please ensure sufficient data is loaded before attempting GWAS execution."
    exit 1
fi

echo "=========================================="
echo "Power Analysis Check PASSED"
echo "Pipeline may proceed to GWAS execution."
echo "=========================================="
exit 0