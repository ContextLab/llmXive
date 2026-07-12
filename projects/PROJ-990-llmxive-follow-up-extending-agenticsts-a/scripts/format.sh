#!/bin/bash
set -e

echo "Running Ruff formatter..."
ruff format code/ tests/

echo "Running Black formatter..."
black code/ tests/

echo "Formatting complete."
