#!/bin/bash
# T043: Power Analysis Gatekeeper
# This script executes the power analysis utility immediately after data loading.
# It enforces FR-012 by halting the pipeline with exit code 1 and the specific
# error message ERR_SAMPLE_SIZE_INSUFFICIENT if the sample size (n) is < 80.
#
# This MUST run BEFORE any GWAS execution (T017).

set -e

# Define paths relative to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
POWER_ANALYSIS_SCRIPT="$PROJECT_ROOT/code/utils/power_analysis.py"

echo "----------------------------------------"
echo "T043: Checking Sample Size Power..."
echo "----------------------------------------"

# Verify the power analysis script exists
if [ ! -f "$POWER_ANALYSIS_SCRIPT" ]; then
    echo "ERROR: Power analysis script not found at $POWER_ANALYSIS_SCRIPT"
    exit 1
fi

# Execute the power analysis
# The script is expected to:
# 1. Read the loaded data (phenotypes/genotypes)
# 2. Calculate power
# 3. If n < 80: Exit with code 1 and print "ERR_SAMPLE_SIZE_INSUFFICIENT"
# 4. If n >= 80: Write result to data/processed/power_analysis.txt and exit 0
python "$POWER_ANALYSIS_SCRIPT"
POWER_EXIT_CODE=$?

if [ $POWER_EXIT_CODE -ne 0 ]; then
    echo "----------------------------------------"
    echo "HALT: Power analysis failed or sample size insufficient."
    echo "The pipeline cannot proceed to GWAS (T017)."
    echo "----------------------------------------"
    # Ensure the specific error message is propagated if the python script printed it
    # The python script itself should handle printing the error, but we ensure the exit code is preserved.
    exit 1
fi

echo "----------------------------------------"
echo "SUCCESS: Sample size requirement met (n >= 80)."
echo "Pipeline can proceed to GWAS execution."
echo "----------------------------------------"

# Exit successfully to allow next pipeline stage
exit 0