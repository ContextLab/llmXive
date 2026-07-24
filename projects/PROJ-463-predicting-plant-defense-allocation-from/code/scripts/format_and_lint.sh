#!/bin/bash
# Script to format and lint the codebase
# Requires: ruff, black installed in the environment

set -e

echo "Running code formatter (black)..."
python -m black code/

echo ""
echo "Running linter (ruff)..."
python -m ruff check code/

echo ""
echo "Formatting and linting complete."