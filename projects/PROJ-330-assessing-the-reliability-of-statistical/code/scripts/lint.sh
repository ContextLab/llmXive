#!/bin/bash
# Linting script for the project
# Runs flake8 and black --check against the codebase

set -e

echo "Running linter (flake8)..."
python -m flake8 code/src code/scripts code/tests

echo "Running formatter check (black --check)..."
python -m black --check --line-length 88 code/src code/scripts code/tests

echo "Linting and formatting checks passed!"
