#!/bin/bash
# Format the codebase using black and ruff-format
set -e

echo "Running Black and Ruff Formatter..."
cd "$(dirname "$0")/.."
black code/
ruff format code/

echo "Formatting complete."
