#!/bin/bash
set -e

echo "Running code formatting (black) and sorting (isort)..."

# Ensure scripts directory exists
mkdir -p scripts

# Run isort to sort imports
python -m isort code/ tests/ --profile black --line-length 88

# Run black to format code
python -m black code/ tests/ --line-length 88

echo "Formatting complete. Run 'scripts/lint.sh' to check for remaining issues."
