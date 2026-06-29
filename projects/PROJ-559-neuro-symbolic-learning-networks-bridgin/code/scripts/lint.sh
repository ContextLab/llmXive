#!/bin/bash
# Script to run linter checks without auto-fixing
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter..."
ruff check code/

echo "Running Black check (dry run)..."
black --check code/

echo "Linting complete."
