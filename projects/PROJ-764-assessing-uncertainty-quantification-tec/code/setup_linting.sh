#!/bin/bash
# Script to initialize linting and formatting tools for the project
# This script assumes the project is in the 'code' directory or run from root

set -e

echo "Installing linting and formatting tools..."
pip install -r requirements.txt

echo "Initializing pre-commit hooks..."
# Ensure we are in the code directory relative to the repo root if needed
# or just run from the directory where .pre-commit-config.yaml lives
pre-commit install

echo "Running initial lint check (ruff)..."
ruff check .

echo "Running initial format check (black)..."
black --check .

echo "Linting and formatting configuration complete."
echo "To run manually:"
echo "  ruff check ."
echo "  black --check ."
echo "To auto-fix:"
echo "  ruff check --fix ."
echo "  black ."