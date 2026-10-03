#!/bin/bash
# Script to run all formatters and linters
# Usage: ./scripts/format.sh

set -e

echo "Running Black formatter..."
black .

echo "Running Ruff linter (auto-fix)..."
ruff check --fix .

echo "Formatting and linting complete."
