#!/bin/bash
# Script to format code and apply linting fixes

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff with autofix..."
ruff check --fix code/ tests/

echo "Formatting complete."
