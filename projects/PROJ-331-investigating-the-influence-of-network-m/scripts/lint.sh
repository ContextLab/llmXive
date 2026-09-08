#!/bin/bash
set -e

echo "Running linter (flake8)..."

# Run flake8
python -m flake8 code/ tests/

echo "Linting complete. All checks passed."
