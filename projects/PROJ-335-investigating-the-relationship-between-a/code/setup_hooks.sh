#!/bin/bash
# Script to initialize pre-commit hooks in the code directory
# Run this from the project root: ./code/setup_hooks.sh

set -e

echo "Installing pre-commit hooks..."

# Ensure pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Error: pre-commit is not installed. Please install it via 'pip install pre-commit'"
    exit 1
fi

# Navigate to code directory where config files are
cd "$(dirname "$0")"

# Initialize the hooks
pre-commit install

echo "Pre-commit hooks installed successfully!"
echo "Hooks will now run automatically on 'git commit'."
