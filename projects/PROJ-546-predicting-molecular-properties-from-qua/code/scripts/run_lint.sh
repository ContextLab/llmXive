#!/bin/bash
# Run linter (ruff) on the codebase

set -e

echo "Running ruff lint check..."
ruff check . --output-format=concise

echo "Lint check completed."
