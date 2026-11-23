#!/bin/bash
# Script to generate the final report for T028
# This script runs the final_report.py module to generate data/results/final_report.json

set -e

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure we're in the code directory
cd code

# Run the final report generation
echo "Generating final report..."
python src/final_report.py

# Verify the output file exists
if [ -f "../data/results/final_report.json" ]; then
    echo "Final report generated successfully: ../data/results/final_report.json"
    echo "Contents:"
    cat ../data/results/final_report.json
else
    echo "ERROR: Final report was not generated!"
    exit 1
fi