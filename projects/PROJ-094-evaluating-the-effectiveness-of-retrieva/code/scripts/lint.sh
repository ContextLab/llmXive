#!/bin/bash
# Script to lint code using Ruff and check formatting with Black
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Checking Black formatting..."
black --check code/ tests/

echo "Linting and formatting checks passed."