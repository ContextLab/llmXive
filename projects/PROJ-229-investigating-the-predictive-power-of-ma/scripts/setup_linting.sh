#!/bin/bash
# Script to install and verify linting and formatting tools

set -e

echo "Installing development dependencies..."
pip install -r requirements-dev.txt

echo "Verifying tool availability..."
black --version
flake8 --version
isort --version

echo "Running initial linting checks on existing code..."
flake8 code/ --max-line-length=88 --ignore=E203,W503 --exclude=__pycache__
isort --check-only --diff code/ tests/
black --check --diff code/ tests/

echo "Linting and formatting setup complete."