#!/bin/bash
set -e

echo "Running black..."
black code/

echo "Running ruff format (if available)..."
ruff format code/ 2>/dev/null || true

echo "Formatting completed."
