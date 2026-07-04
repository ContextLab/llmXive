#!/bin/bash
# Run linting checks
set -e
echo "Running flake8..."
python -m flake8 .
echo "Running mypy..."
python -m mypy code/ --ignore-missing-imports
echo "Linting complete."
