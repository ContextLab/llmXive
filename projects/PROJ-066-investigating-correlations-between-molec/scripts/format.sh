#!/bin/bash
# Script to run formatting and linting tools
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter (fix mode)..."
ruff check code/ tests/ --fix

echo "Running Ruff linter (strict mode)..."
ruff check code/ tests/

echo "Formatting and linting complete."
