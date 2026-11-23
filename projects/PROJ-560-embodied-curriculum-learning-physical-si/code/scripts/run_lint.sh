#!/bin/bash
# Script to run linter checks using Ruff
# Exits with non-zero status if errors are found

set -e

echo "Running Ruff linter..."
ruff check code/src/ code/tests/
echo "Lint check passed."
