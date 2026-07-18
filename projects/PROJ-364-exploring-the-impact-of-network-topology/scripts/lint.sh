#!/bin/bash
# Run only linter checks

set -e

echo "Running Ruff linter..."
ruff check .

echo "Linting complete."
