#!/bin/bash
# Format code using Black and sort imports using Ruff

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter and fixer..."
ruff check --fix code/ tests/

echo "Formatting complete."
