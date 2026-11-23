#!/bin/bash
# Run all linting and formatting checks

set -e

echo "=========================================="
echo "Running Full Code Quality Checks"
echo "=========================================="

echo "1. Running Linter (ruff)..."
ruff check .

echo ""
echo "2. Running Formatter (black) --check..."
black --check .

echo ""
echo "=========================================="
echo "All checks passed successfully!"
echo "=========================================="