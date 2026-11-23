#!/bin/bash
# Run formatter to fix code style issues
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff fixer (if applicable)..."
ruff check --fix code/ tests/ || true

echo "Formatting complete."