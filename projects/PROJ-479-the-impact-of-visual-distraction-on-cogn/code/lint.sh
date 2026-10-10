#!/usr/bin/env bash
# Linting script for the project
# Runs ruff (fast linting) followed by black (code formatting)
set -e

# Ensure we are in the repository root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
cd "$REPO_ROOT"

echo "Running ruff..."
ruff code tests specs

echo "Running black..."
black code tests specs

echo "Linting completed successfully."
