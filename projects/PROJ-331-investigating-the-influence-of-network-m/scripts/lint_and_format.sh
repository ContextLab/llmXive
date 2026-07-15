#!/bin/bash
# Script to run linters and formatters on the project code.
# Usage: ./scripts/lint_and_format.sh [--fix]

set -e

FIX_MODE=false
if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

echo "Running linting and formatting checks..."

if [ "$FIX_MODE" = true ]; then
    echo "Fixing code style with black and isort..."
    isort code/ tests/
    black code/ tests/
else
    echo "Checking code style (dry run)..."
    isort --check-only code/ tests/
    black --check code/ tests/
fi

echo "Running flake8 linting..."
flake8 code/ tests/

echo "Linting and formatting checks completed successfully."