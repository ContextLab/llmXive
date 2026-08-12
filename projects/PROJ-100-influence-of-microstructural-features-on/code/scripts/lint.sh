#!/bin/bash
# Run linters: ruff and flake8
set -e

echo "Running ruff linter..."
ruff check code/

echo "Running flake8 linter..."
flake8 code/

echo "Linting complete."
