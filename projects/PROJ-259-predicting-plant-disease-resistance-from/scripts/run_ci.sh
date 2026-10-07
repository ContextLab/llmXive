#!/bin/bash
# CI-specific wrapper script for the plant disease resistance prediction pipeline.
# Sets resource constraints and executes the full pipeline.
#
# This script ensures that `code/utils/measure_resources.py` and `code/main.py`
# respect the defined memory and runtime limits.

set -e

# Configuration: Hard limits for CI environment (GitHub Actions free-tier)
export MAX_MEMORY_GB=7
export MAX_RUNTIME_HOURS=6

# Optional: Set a fixed random seed for reproducibility if not already set
export PYTHONHASHSEED=42

echo "=== Plant Disease Resistance Prediction Pipeline - CI Execution ==="
echo "Start Time: $(date)"
echo "Max Memory Limit: ${MAX_MEMORY_GB} GB"
echo "Max Runtime Limit: ${MAX_RUNTIME_HOURS} hours"
echo "---------------------------------------------------------------"

# Change to project root (assuming script is run from root or project dir)
# If running via docker, this should be the mounted project directory
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "$PROJECT_ROOT"

echo "Project Root: $PROJECT_ROOT"
echo "Starting pipeline execution..."

# Execute the main pipeline entry point
# The main.py script is expected to import utils/measure_resources.py
# which will read MAX_MEMORY_GB and MAX_RUNTIME_HOURS to enforce limits.
python code/main.py

EXIT_CODE=$?

echo "---------------------------------------------------------------"
echo "End Time: $(date)"
if [ $EXIT_CODE -eq 0 ]; then
    echo "Pipeline completed successfully within resource constraints."
else
    echo "Pipeline failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE