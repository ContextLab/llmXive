#!/bin/bash
# Format code with Black and Ruff
set -e

echo "Running Black formatter..."
black projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/

echo "Running Ruff linter (fix mode)..."
ruff check --fix projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/

echo "Running Ruff formatter (if enabled)..."
ruff format projects/PROJ-864-llmxive-follow-up-extending-improved-lar/code/

echo "Formatting complete."
