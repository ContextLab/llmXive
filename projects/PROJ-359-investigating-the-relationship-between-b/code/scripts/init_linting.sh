#!/bin/bash
set -e

echo "Initializing linting and formatting tools..."

# Install pre-commit if not present
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi

# Install black and ruff if not present (though pyproject.toml lists dependencies, pre-commit hooks need them locally too if not using system)
# The pre-commit hooks will install their own versions usually, but let's ensure the tools are available for manual runs
pip install black ruff

# Initialize pre-commit hooks
echo "Installing pre-commit hooks..."
cd "$(dirname "$0")/.."
pre-commit install

echo "Linting and formatting setup complete."
echo "Run 'pre-commit run --all-files' to check all files."