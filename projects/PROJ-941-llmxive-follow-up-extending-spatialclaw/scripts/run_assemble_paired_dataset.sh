#!/bin/bash
# Script to execute the final paired dataset assembly (T047c)
# This script runs the assembly logic implemented in T047a

set -e

# Change to project root directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Running Final Paired Dataset Assembly (T047c) ==="
echo "Project root: $PROJECT_ROOT"

# Check if required input files exist
if [ ! -f "data/power_config.yaml" ]; then
    echo "ERROR: data/power_config.yaml not found"
    exit 1
fi

if [ ! -f "results/logs/baseline_run.json" ]; then
    echo "ERROR: results/logs/baseline_run.json not found"
    echo "Please ensure T052b (Execute Full Pipeline) has completed successfully."
    exit 1
fi

if [ ! -d "results/runs" ]; then
    echo "ERROR: results/runs directory not found"
    echo "Please ensure T052b (Execute Full Pipeline) has completed successfully."
    exit 1
fi

# Count run files
RUN_COUNT=$(ls -1 results/runs/run_*.json 2>/dev/null | wc -l)
echo "Found $RUN_COUNT run files in results/runs/"

if [ "$RUN_COUNT" -lt 1 ]; then
    echo "ERROR: No run files found in results/runs/"
    exit 1
fi

echo "Running assembly script..."
python code/analysis/assemble_paired_dataset.py \
    --config data/power_config.yaml \
    --baseline results/logs/baseline_run.json \
    --2d-runs results/runs \
    --output results/analysis/final_paired_dataset.csv

# Verify output file was created
if [ -f "results/analysis/final_paired_dataset.csv" ]; then
    echo "SUCCESS: Final paired dataset created at results/analysis/final_paired_dataset.csv"
    echo "Row count:"
    wc -l results/analysis/final_paired_dataset.csv
else
    echo "ERROR: Output file was not created"
    exit 1
fi

echo "=== T047c Execution Complete ==="
