#!/bin/bash
# Run all linting and formatting checks
# Usage: ./scripts/run_linting.sh [--fix]

set -e

echo "Running linting and formatting checks..."

if [[ "$1" == "--fix" ]]; then
    echo "Running in fix mode..."
    python -m black code/ tests/
    echo "Formatting applied. Re-running flake8 to check for remaining issues..."
    python -m flake8 code/ tests/
else
    echo "Running in check mode..."
    python -m black --check code/ tests/
    python -m flake8 code/ tests/
fi

echo "Linting checks completed."
