#!/bin/bash
# Lint code with Ruff
set -e

echo "Running Ruff linter..."
ruff check projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/

echo "Running Black check (dry-run)..."
black --check projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/

echo "Linting complete."