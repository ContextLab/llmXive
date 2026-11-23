#!/bin/bash
# Script to automatically fix linting and formatting issues.
# This script is intended to be run from the project root directory.

set -e

echo "Running Ruff Linter (fix mode)..."
ruff check --fix .

echo "Running Black Formatter..."
black .

echo "Linting and formatting fixes applied."
