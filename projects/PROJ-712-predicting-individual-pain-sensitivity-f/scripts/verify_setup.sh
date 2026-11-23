#!/bin/bash
# Script to verify that the required directories exist after running setup_directories.py

set -e

REQUIRED_DIRS=(
    "data/raw"
    "data/processed"
    "artifacts"
    "state"
    "code"
    "tests"
)

echo "Verifying project directory structure..."
all_ok=true

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir exists"
    else
        echo "✗ $dir is MISSING"
        all_ok=false
    fi
done

if [ "$all_ok" = true ]; then
    echo "All required directories verified."
    exit 0
else
    echo "Verification failed: Some directories are missing."
    exit 1
fi