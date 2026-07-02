#!/bin/bash
# Auto-format code using Black and Ruff

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter with auto-fix..."
ruff check --fix code/

echo "Formatting complete."
