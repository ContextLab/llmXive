#!/bin/bash
set -e

echo "Running Black Formatter..."
black code/

echo "Running Ruff Format (Alternative)..."
ruff format code/

echo "Formatting complete."
