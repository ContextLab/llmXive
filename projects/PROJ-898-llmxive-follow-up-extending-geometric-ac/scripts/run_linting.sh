#!/bin/bash
# Script to run linting and formatting checks
# Usage: bash scripts/run_linting.sh [--fix]

set -e

FIX_MODE=false
if [ "$1" == "--fix" ]; then
    FIX_MODE=true
    echo "Running in fix mode..."
fi

echo "========================================="
echo "Running Linting and Formatting Checks"
echo "========================================="

# Run pre-commit if available
if command -v pre-commit &> /dev/null; then
    echo "Running pre-commit..."
    if [ "$FIX_MODE" = true ]; then
        pre-commit run --all-files --hook-stage manual
    else
        pre-commit run --all-files
    fi
else
    echo "pre-commit not found, running tools directly..."

    # Run ruff
    echo "Running ruff check..."
    if [ "$FIX_MODE" = true ]; then
        ruff check --fix code/ tests/
    else
        ruff check code/ tests/
    fi

    # Run black
    echo "Running black check..."
    if [ "$FIX_MODE" = true ]; then
        black code/ tests/
    else
        black --check code/ tests/
    fi
fi

echo "========================================="
echo "Linting and formatting checks complete!"
echo "========================================="
