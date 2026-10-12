#!/usr/bin/env bash
# Linting and formatting script for the BMG project
# Runs ruff, flake8, and black in check mode.

set -e  # Exit immediately if a command exits with a non-zero status

echo "Running Ruff lint..."
ruff check .

echo "Running Flake8 lint..."
flake8 .

echo "Running Black formatting check..."
black --check .

echo "All linters passed successfully."