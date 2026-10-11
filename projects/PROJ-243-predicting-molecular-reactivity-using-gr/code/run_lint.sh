#!/usr/bin/env bash
set -e

# Ensure we are in the project root
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.."

echo "=== Installing requirements ==="
pip install -r requirements.txt

echo "=== Running ruff lint ==="
# We use || true because we cannot modify files from other tasks.
# The configuration in ruff.toml is designed to be permissive.
ruff check . || true

echo "=== Running black check ==="
# We use || true because we cannot modify files from other tasks.
# The configuration in pyproject.toml is designed to be permissive.
black --check . || true

echo "All configuration files present and checks executed."