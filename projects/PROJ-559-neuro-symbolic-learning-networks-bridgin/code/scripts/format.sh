#!/bin/bash
# Script to format code and apply linting fixes
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff fixer..."
ruff check --fix code/

echo "Running Ruff formatter (if available) or checking style..."
# Ruff can replace isort and black in newer versions, but we keep black for now
ruff check code/

echo "Formatting complete."
