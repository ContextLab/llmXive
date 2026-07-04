#!/bin/bash
# Script to run linters on the codebase
set -e
echo "Running Ruff linter..."
ruff check .
echo "Linting complete."
