#!/bin/bash
# Run linter checks without auto-fixing
set -e

echo "Running Ruff linter..."
ruff check code/

echo "Linting complete."
