#!/bin/bash
# Format code with Black and sort imports with Ruff
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff to fix autofixable issues..."
ruff check --fix code/ tests/

echo "Formatting complete."
