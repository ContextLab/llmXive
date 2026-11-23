#!/bin/bash
# Script to run linting and formatting checks for the project.
# This script ensures code quality by running flake8 and black.

set -e

echo "Running flake8 linting checks..."
flake8 code/ tests/ --config=pyproject.toml

echo "Running black formatting check (check mode)..."
black --check --config=pyproject.toml code/ tests/

echo "Linting and formatting checks passed."
