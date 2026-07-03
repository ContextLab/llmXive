#!/bin/bash
set -e

echo "Running flake8..."
flake8 code/ tests/

echo "Running black (check only)..."
black --check code/ tests/

echo "Running isort (check only)..."
isort --check-only code/ tests/

echo "Linting complete."
