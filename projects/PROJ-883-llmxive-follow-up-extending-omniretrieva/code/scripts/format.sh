#!/bin/bash
# Format code with Black and lint with Ruff
set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter (check only)..."
ruff check code/

echo "Running Ruff formatter (if available)..."
if command -v ruff &> /dev/null; then
    ruff format --check code/ || true
fi

echo "Formatting and linting complete."
