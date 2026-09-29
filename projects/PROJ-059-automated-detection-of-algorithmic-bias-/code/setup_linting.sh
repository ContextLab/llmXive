#!/bin/bash
# Script to initialize linting and formatting tools for the project
# Task: T003 - Configure linting (ruff) and formatting (black) tools

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Initializing pre-commit hooks..."
pre-commit install

echo "Running initial lint check..."
ruff check code/ --fix || true

echo "Running initial format check..."
black --check code/ || true

echo "Linting and formatting configuration complete."
echo "To run manually:"
echo "  ruff check code/"
echo "  black code/"
echo "  pre-commit run --all-files"
