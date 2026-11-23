#!/bin/bash
# Script to lint code using Ruff and Flake8
# Usage: ./scripts/lint_code.sh

set -e

echo "Linting code with Ruff..."
ruff check code/

echo "Linting code with Flake8..."
flake8 code/

echo "Linting complete."
