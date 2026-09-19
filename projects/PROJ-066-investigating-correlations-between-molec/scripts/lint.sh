#!/bin/bash
# Script to run linters (Ruff) and type checkers (optional)
# Usage: ./scripts/lint.sh

set -e

echo "Running Ruff check..."
ruff check code/ tests/

echo "Linting complete."
