#!/bin/bash
# Script to format code and check linting for PROJ-538
# Usage: ./scripts/format_code.sh [check|fix]

set -e

MODE="${1:-fix}"

echo "Running code quality tools for PROJ-538..."

if [ "$MODE" == "fix" ]; then
    echo "Formatting code with Black..."
    black code/ tests/
    
    echo "Fixing linting issues with Ruff..."
    ruff check --fix code/ tests/
    
    echo "Sorting imports with Ruff..."
    ruff check --select I --fix code/ tests/
    
    echo "Formatting complete."
elif [ "$MODE" == "check" ]; then
    echo "Checking code formatting with Black..."
    black --check code/ tests/
    
    echo "Checking linting with Ruff..."
    ruff check code/ tests/
    
    echo "Checking import sorting..."
    ruff check --select I code/ tests/
    
    echo "All checks passed."
else
    echo "Invalid mode: $MODE. Use 'fix' or 'check'."
    exit 1
fi
