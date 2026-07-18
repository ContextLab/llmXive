#!/bin/bash
# Run formatter (ruff/black) and linter auto-fix

set -e

echo "Running ruff format..."
ruff format code/ tests/

echo "Running ruff check --fix..."
ruff check --fix code/ tests/

echo "Formatting and auto-fix complete."
