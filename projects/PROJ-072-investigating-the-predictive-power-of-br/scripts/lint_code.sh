#!/bin/bash
# Script to lint code using Ruff
set -e

echo "Running Ruff linter..."
ruff check code/ tests/ scripts/

echo "Linting complete."
