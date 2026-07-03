#!/bin/bash
# Script to run linting and formatting checks
# Usage: ./scripts/lint_and_format.sh [--fix]

set -e

echo "Running flake8..."
flake8 src/ tests/

echo "Running isort (check mode)..."
isort src/ tests/ --check-only

echo "Running black (check mode)..."
black --check src/ tests/

if [ "$1" == "--fix" ]; then
    echo "Fixing formatting issues..."
    isort src/ tests/
    black src/ tests/
    echo "Formatting fixed."
else
    echo "Lint and format check complete. Run with --fix to auto-correct."
fi
