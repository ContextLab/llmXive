#!/bin/bash
# Script to run linting and formatting checks
# Usage: ./scripts/check_lint.sh

set -e

echo "Running Ruff (lint)..."
ruff check .

echo "Running Black (format check)..."
black --check .

echo "Running Mypy (type check)..."
mypy src/

echo "All linting checks passed."