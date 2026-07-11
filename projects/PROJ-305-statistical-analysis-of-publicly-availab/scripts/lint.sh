#!/bin/bash
# Script to lint the codebase without auto-fixing

set -e

echo "Running Ruff linter..."
ruff check .

echo "Running Black check (diff mode)..."
black --check .

echo "Linting complete."
