#!/bin/bash
# Script to run black and ruff for formatting and linting

set -e

echo "Running Black formatter..."
black projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
black projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/

echo "Running Ruff linter (check mode)..."
ruff check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
ruff check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/

echo "Running Ruff format check..."
ruff format --check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
ruff format --check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/

echo "Formatting and linting completed successfully."
