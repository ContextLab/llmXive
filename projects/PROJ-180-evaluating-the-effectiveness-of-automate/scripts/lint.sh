#!/bin/bash
# Linting script using Ruff
set -e
echo "Running Ruff linter..."
ruff check code/ tests/
echo "Linting complete."
