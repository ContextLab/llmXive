#!/bin/bash
# Script to run the full pipeline timing verification for Task T042
# Usage: ./code/run_pipeline_timing.sh [--dry-run]

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "=========================================="
echo "Pipeline Timing Verification (T042)"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Start Time: $(date)"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Run the timing verification script
if [ "$1" == "--dry-run" ]; then
    echo "Running in DRY-RUN mode (no actual execution)..."
    echo ""
    python code/utils/timing.py --dry-run
else
    echo "Running FULL pipeline timing verification..."
    echo "This may take several hours depending on data availability."
    echo ""
    python code/utils/timing.py
fi

EXIT_CODE=$?

echo ""
echo "End Time: $(date)"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ T042 VALIDATION PASSED: Pipeline runtime is within 6-hour limit."
else
    echo "❌ T042 VALIDATION FAILED: Pipeline runtime exceeded limit or errors occurred."
fi

exit $EXIT_CODE