#!/bin/bash
# Script to install and configure linting tools (ruff, black, pre-commit)
# for the llmXive project.

set -e

echo "Installing linting tools..."
pip install ruff black pre-commit

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Linting configuration complete."
echo "Run 'pre-commit run --all-files' to check all files."
