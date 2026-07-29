#!/bin/bash
# Run linters without fixing
set -e
echo "Running Ruff..."
ruff check code/
echo "Running Flake8..."
flake8 code/ --max-line-length=100
echo "Linting complete."