#!/bin/bash
# Script to run the scaling study for T027
# Executes src/experiments/scaling.py with appropriate parameters
# and verifies the output file is created.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Running scaling study..."

# Run the scaling study script
python code/src/experiments/scaling.py \
    --epochs 10 \
    --batch-size 32 \
    --lr 1e-3 \
    --device cpu \
    --output data/results/scaling_results.json

# Verify output file exists
if [ -f "data/results/scaling_results.json" ]; then
    echo "SUCCESS: Scaling results file created at data/results/scaling_results.json"
    echo "Contents:"
    cat data/results/scaling_results.json
else
    echo "ERROR: Scaling results file not found at data/results/scaling_results.json"
    exit 1
fi