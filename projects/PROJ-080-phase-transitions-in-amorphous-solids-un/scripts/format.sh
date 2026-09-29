#!/bin/bash
# Script to format code with Black and sort imports with Ruff/Isort
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff check and auto-fix..."
ruff check --fix code/ tests/

echo "Formatting complete."
