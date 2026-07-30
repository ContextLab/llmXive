#!/bin/bash
# Lint the codebase using ruff
set -e

echo "Running Ruff Linter..."
cd "$(dirname "$0")/.."
ruff check code/

echo "Linting complete."
