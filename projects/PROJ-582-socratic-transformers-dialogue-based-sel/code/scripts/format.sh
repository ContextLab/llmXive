#!/bin/bash
# Script to run linter (ruff) and formatter (black) on the project.
# This script is intended to be run from the project root directory.

set -e

echo "Running Ruff Linter..."
ruff check .

echo "Running Black Formatter (check mode)..."
black --check .

echo "Linting and formatting checks passed."
