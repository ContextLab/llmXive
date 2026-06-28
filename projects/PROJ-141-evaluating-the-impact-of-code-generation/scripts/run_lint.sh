#!/bin/bash
# Script to run linting and formatting checks

set -e

echo "=== Running Linting and Formatting Checks ==="
echo ""

# Check if tools are installed
if ! command -v black &> /dev/null; then
    echo "ERROR: black is not installed. Run: pip install black"
    exit 1
fi

if ! command -v flake8 &> /dev/null; then
    echo "ERROR: flake8 is not installed. Run: pip install flake8"
    exit 1
fi

echo "✓ Tools available"
echo ""

# Run flake8
echo "Running flake8..."
flake8 code/ tests/ || {
    echo "✗ flake8 found issues"
    exit 1
}
echo "✓ flake8 passed"
echo ""

# Run black check
echo "Running black --check..."
black --check code/ tests/ || {
    echo "✗ black found formatting issues"
    echo "Run 'make format' or 'black code/ tests/' to fix"
    exit 1
}
echo "✓ black passed"
echo ""

echo "=== All linting checks passed ==="
