#!/bin/bash
set -e
echo "Running Black formatter..."
black code/
echo "Running Ruff linter (fix mode)..."
ruff check --fix code/
echo "Formatting and linting complete."
