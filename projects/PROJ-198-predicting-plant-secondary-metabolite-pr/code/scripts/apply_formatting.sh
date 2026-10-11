#!/bin/bash
set -e

echo "Applying Black formatting..."
black .

echo "Applying Ruff fixes..."
ruff --fix .

echo "Verifying Ruff..."
ruff --quiet .

echo "Verifying Black..."
black --check .

echo "Linting and formatting verification successful."