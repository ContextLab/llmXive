#!/bin/bash
# Script to run formatting (black) and linting (ruff) on the project.
# Exit codes: 0 = success, 1 = linting/formatting issues found or errors.

set -e

echo "Running Black formatter..."
black code/ tests/

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting and formatting checks passed."
