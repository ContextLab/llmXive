#!/bin/bash
# Script to run linting checks using ruff
# Exit on error
set -e

echo "Running Ruff linter..."
ruff check code/

echo "Linting complete."
