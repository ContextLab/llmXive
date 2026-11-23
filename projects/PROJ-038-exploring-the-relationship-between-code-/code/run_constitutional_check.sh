#!/bin/bash
# Script to run the Constitutional Check (Task T000b)
# This script halts the pipeline if the amendment marker is missing.

set -e

echo "Running Constitutional Amendment Check (T000b)..."

# Change to the code directory to ensure relative paths work if needed
cd "$(dirname "$0")"

# Run the Python verification script
python src/constitutional_check.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Constitutional check passed. Proceeding with pipeline."
    exit 0
else
    echo "✗ Constitutional check failed. Halting pipeline."
    exit 1
fi
