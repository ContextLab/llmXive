#!/bin/bash
set -e
echo "Running code formatter (black)..."
black code/src/ code/tests/ code/scripts/
echo "Running code linter (ruff)..."
ruff check code/src/ code/tests/ code/scripts/
echo "Formatting and linting complete."
