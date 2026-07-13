#!/bin/bash
set -e
echo "Running Black formatter..."
black .
echo "Running Ruff linter (auto-fix)..."
ruff check --fix .
echo "Formatting and linting complete."
