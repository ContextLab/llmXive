#!/bin/bash
# Script to format code using Black and sort imports using Ruff
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter and auto-fixer..."
ruff check --fix code/ tests/

echo "Formatting complete."
