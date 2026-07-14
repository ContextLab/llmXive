#!/bin/bash
# Setup script for linting and formatting tools
# This script installs flake8, black, and isort, then runs a quick check

set -e

echo "Installing linting and formatting tools..."
pip install -q flake8 black isort pytest-cov

echo "Running initial flake8 check (ignoring common project exclusions)..."
flake8 code/ --max-line-length=88 --exclude=code/setup_project_structure.py,code/setup_linting.sh --ignore=E203,W503 --show-source --statistics || echo "Linting issues found (expected in initial run)"

echo "Running black check (dry-run)..."
black --check --line-length 88 code/ --exclude=code/setup_project_structure.py,code/setup_linting.sh || echo "Formatting fixes needed (run 'black code/ --exclude=code/setup_project_structure.py,code/setup_linting.sh' to apply)"

echo "Linting and formatting configuration complete."
echo "To run flake8 manually: flake8 code/"
echo "To run black manually: black code/"
echo "To run isort manually: isort code/"