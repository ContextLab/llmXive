#!/usr/bin/env bash
# Script to run linting and formatting checks for the project.
# Usage: ./scripts/lint_format.sh [--fix]
#
# If --fix is provided, it will automatically format code and run isort.
# Otherwise, it only checks for issues.

set -e

FIX_MODE=false
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

echo "Running linting and formatting checks..."

# Check flake8
echo "Checking flake8..."
flake8 code/

if [ "$FIX_MODE" = true ]; then
    echo "Running black (auto-format)..."
    black code/

    echo "Running isort..."
    isort code/
else
    echo "Running black (check only)..."
    black --check code/

    echo "Running isort (check only)..."
    isort --check code/
fi

echo "Linting and formatting checks completed successfully."
