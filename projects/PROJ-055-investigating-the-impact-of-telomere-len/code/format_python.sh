#!/bin/bash
# Script to format Python code using ruff (black + isort functionality)

set -e

echo "Running Python code formatter (ruff)..."

# Format code directory
ruff format code/

# Lint code directory
ruff check --fix code/

echo "Python code formatting complete."
