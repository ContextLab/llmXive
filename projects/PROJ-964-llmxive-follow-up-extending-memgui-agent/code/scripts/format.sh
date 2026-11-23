#!/bin/bash
# Format code using Black and lint using Ruff
set -e

echo "Running Black formatter..."
black .

echo "Running Ruff linter (check only)..."
ruff check .

echo "Formatting and linting complete."
