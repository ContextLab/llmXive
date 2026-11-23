#!/bin/bash
# Full validation script: lint and format check
# This script ensures code quality before merging

set -e

echo "=== Starting Code Validation ==="

# Check formatting
echo "Checking formatting..."
if ! black --check code/src/ code/tests/; then
    echo "ERROR: Code is not formatted. Run 'bash code/scripts/run_format.sh' to fix."
    exit 1
fi

# Run linter
echo "Running linter..."
if ! ruff check code/src/ code/tests/; then
    echo "ERROR: Linter errors found. Fix issues before committing."
    exit 1
fi

echo "=== Validation Successful ==="