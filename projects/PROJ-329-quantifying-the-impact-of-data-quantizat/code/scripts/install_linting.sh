#!/bin/bash
set -e

echo "Installing linting and formatting tools..."

# Install pre-commit hooks
pre-commit install

echo "Linting configuration complete."
echo "Run 'pre-commit run --all-files' to check all files."