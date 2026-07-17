#!/bin/bash
# Script to run linter checks only (without auto-fixing)
set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Running Black check (diff mode)..."
black --check code/ tests/

echo "Checks complete."