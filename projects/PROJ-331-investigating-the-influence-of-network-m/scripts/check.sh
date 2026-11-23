#!/bin/bash
set -e

echo "Running all checks: format, lint, and tests..."

# Run linter
python -m flake8 code/ tests/

# Run type checker (mypy) if available
if command -v mypy &> /dev/null; then
    echo "Running mypy..."
    python -m mypy code/ --ignore-missing-imports
else
    echo "mypy not found, skipping type checking."
fi

# Run tests if pytest is available
if command -v pytest &> /dev/null; then
    echo "Running tests..."
    python -m pytest tests/ -v
else
    echo "pytest not found, skipping tests."
fi

echo "All checks completed successfully."