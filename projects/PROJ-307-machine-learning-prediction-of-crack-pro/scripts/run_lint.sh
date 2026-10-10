#!/usr/bin/env bash
set -euo pipefail

# Ensure the virtual environment is active (the CI should have already installed the requirements)
echo "Running ruff lint..."
ruff .

echo "Running black check..."
black --check .

echo "Linting and formatting checks passed."
