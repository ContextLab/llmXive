#!/bin/bash
# Lint and format check script for the project
# Runs ruff (linting) and black (formatting check)

set -e

echo "Running Ruff linter..."
ruff check .

echo "Running Black format check..."
black --check .

echo "Lint and format checks passed."
