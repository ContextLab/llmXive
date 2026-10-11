#!/usr/bin/env bash
set -e

# Ensure we are in the project root
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.."

echo "=== Installing requirements ==="
pip install -r requirements.txt

echo "=== Running ruff lint ==="
ruff check .

echo "=== Running black check ==="
black --check .

echo "All checks passed successfully."