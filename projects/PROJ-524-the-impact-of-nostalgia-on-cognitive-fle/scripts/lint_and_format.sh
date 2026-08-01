#!/bin/bash
# Script to run linting and formatting checks
# Usage: ./scripts/lint_and_format.sh

set -e

echo "Running Ruff Linter..."
ruff check code/ tests/

echo "Running Black Formatter (Check mode)..."
black --check code/ tests/

echo "Running Ruff Format (Check mode)..."
ruff format --check code/ tests/

echo "All linting and formatting checks passed."
