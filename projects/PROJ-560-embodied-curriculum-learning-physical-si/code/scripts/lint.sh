#!/bin/bash
set -e
echo "Running Ruff linter..."
ruff check code/
echo "Running MyPy type checker..."
mypy code/ --ignore-missing-imports
echo "Linting and type checking complete."