#!/bin/bash
# Script to run linting checks without auto-fix
# Usage: ./scripts/lint.sh

set -e

echo "Running Black check (dry run)..."
black --check code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting complete."
