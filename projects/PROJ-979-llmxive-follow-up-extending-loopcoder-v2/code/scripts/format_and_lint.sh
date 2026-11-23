#!/bin/bash
# Script to run formatting and linting checks for the project
# Usage: ./scripts/format_and_lint.sh

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter..."
ruff check code/

echo "Running Flake8 linter (optional check)..."
flake8 code/ || true

echo "Formatting and linting complete."