#!/bin/bash
# Script to run linters without auto-fixing
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter (check only)..."
ruff check .

echo "Running Black check (no write)..."
black --check .

echo "Linting complete."