#!/bin/bash
# Lint codebase using Ruff

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting complete."
