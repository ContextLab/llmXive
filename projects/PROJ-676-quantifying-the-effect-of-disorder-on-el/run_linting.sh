#!/bin/bash
# Linting script for PROJ-676
# Executes flake8 and black --check on the code/ directory.
# Fails the build if any violations are found.

set -e

echo "Running linters on code/ directory..."

# Check formatting with black
echo "Checking black formatting..."
black --check code/

# Check style with flake8
echo "Checking flake8 style..."
flake8 code/

echo "All linting checks passed."
