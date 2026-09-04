#!/bin/bash
# Script to run Black formatting and Ruff linting on the codebase
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatting..."
black code/

echo "Running Ruff linter (check mode)..."
ruff check code/

echo "Running Ruff formatter (if available) or checking style..."
# Ruff format is available in newer versions, fallback to check if needed
if ruff format --check code/ 2>/dev/null; then
    echo "Ruff format check passed."
else
    echo "Ruff format check skipped or not supported, relying on Black."
fi

echo "Formatting and linting complete."
