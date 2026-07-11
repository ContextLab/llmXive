#!/bin/bash
# Script to format code using Black and Ruff
set -e

echo "Running Black formatter..."
black code/ tests/ scripts/

echo "Running Ruff linter (fix mode)..."
ruff check --fix code/ tests/ scripts/

echo "Formatting complete."
