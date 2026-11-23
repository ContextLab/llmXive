#!/bin/bash
# Script to execute the Kernel Blockage Final Audit (T050)
# This script runs the audit and ensures the output file is generated.

set -e

echo "Running Kernel Blockage Final Audit (T050)..."

# Ensure results/analysis directory exists
mkdir -p results/analysis

# Run the audit script
python code/utils/kernel_audit.py --logs-dir results/logs --output results/analysis/kernel_audit.txt

# Check exit code
if [ $? -eq 0 ]; then
    echo "Audit PASSED."
    cat results/analysis/kernel_audit.txt
    exit 0
else
    echo "Audit FAILED."
    cat results/analysis/kernel_audit.txt
    exit 1
fi