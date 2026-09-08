#!/bin/bash
# Lint code using Ruff
set -e

echo "Running Ruff linter..."
ruff check .

echo "Linting complete."