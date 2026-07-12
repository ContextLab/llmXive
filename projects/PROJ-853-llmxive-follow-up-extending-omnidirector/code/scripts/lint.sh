#!/bin/bash
# Run linting checks
set -e
cd "$(dirname "$0")/.."
echo "Running Ruff check..."
ruff check code/
echo "Running Black check (diff)..."
black --check code/
echo "Linting complete."
