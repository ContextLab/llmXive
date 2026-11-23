#!/bin/bash
# Script to format code and run linter checks
set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Formatting and linting complete."
