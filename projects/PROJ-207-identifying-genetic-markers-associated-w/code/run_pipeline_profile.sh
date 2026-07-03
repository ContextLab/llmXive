#!/bin/bash
# T041: Run pipeline profiling script
# This script executes the pipeline profiler and generates data/processed/profile_report.txt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Running pipeline profiler..."
python code/utils/profile_pipeline.py --output data/processed/profile_report.txt

if [ -f "data/processed/profile_report.txt" ]; then
    echo "Profile report generated successfully."
    echo "Report location: data/processed/profile_report.txt"
else
    echo "ERROR: Profile report was not generated."
    exit 1
fi
