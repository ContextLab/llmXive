#!/bin/bash
# Script to format code with Black and lint with Ruff
# Usage: ./scripts/format_and_lint.sh

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter (check only)..."
ruff check code/

echo "Linting and formatting complete."
