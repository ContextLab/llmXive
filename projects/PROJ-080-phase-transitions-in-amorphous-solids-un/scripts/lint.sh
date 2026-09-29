#!/bin/bash
# Script to run linter checks without auto-fix
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (diff mode)..."
black --check code/ tests/

echo "Linting complete. If errors were reported, run ./scripts/format.sh to fix."