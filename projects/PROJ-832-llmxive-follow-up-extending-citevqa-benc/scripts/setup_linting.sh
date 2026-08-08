#!/bin/bash
set -e

echo "Installing pre-commit hooks..."
pip install pre-commit ruff black
pre-commit install

echo "Linting and formatting code..."
pre-commit run --all-files

echo "Linting and formatting setup complete."