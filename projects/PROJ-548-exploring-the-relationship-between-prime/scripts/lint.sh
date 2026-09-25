#!/bin/bash
# Lint codebase with Ruff
set -e

echo "Running Ruff linter..."
ruff check code/

echo "Linting complete."
