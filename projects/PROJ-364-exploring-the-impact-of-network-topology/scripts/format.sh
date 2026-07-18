#!/bin/bash
# Format codebase with Black and lint with Ruff

set -e

echo "Running Black formatter..."
black .

echo "Running Ruff linter..."
ruff check .

echo "Formatting and linting complete."
