#!/bin/bash
# Verification script for T001
# Checks that required directories exist and are writable.
# Run this from the project root.

set -e

echo "Verifying project directory structure..."

dirs=(
    "code"
    "data"
    "state"
    "output"
    "tests"
    "docs"
)

failed=0

for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        if [ -w "$dir" ]; then
            echo "[OK] $dir exists and is writable."
        else
            echo "[FAIL] $dir exists but is NOT writable."
            failed=1
        fi
    else
        echo "[FAIL] $dir does not exist."
        failed=1
    fi
done

if [ $failed -eq 0 ]; then
    echo "All required directories verified successfully."
    exit 0
else
    echo "Verification failed."
    exit 1
fi
