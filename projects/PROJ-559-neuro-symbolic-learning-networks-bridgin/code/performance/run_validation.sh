#!/bin/bash
# Script to run the full optimization validation pipeline
# Ensures the entire pipeline operates within the 7GB RAM limit

set -e

echo "=== Starting Optimization Validation ==="
echo "Memory Limit: 7GB (7168 MB)"

# Run the validation entry point
python code/performance/run_optimization.py

echo "=== Validation Complete ==="
