#!/bin/bash
set -e

# Ensure we are running from the project root (where code/ is located)
# The script is expected to be run as: ./code/scripts/format.sh
# or from the root: ./code/scripts/format.sh

echo "Running Black formatter..."
black .

echo "Running Ruff linter (fix mode)..."
ruff check --fix .

echo "Formatting and linting complete."
