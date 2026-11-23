#!/bin/bash
# Run linting and formatting checks for the project

set -e

echo "Running Black format check..."
black --check --line-length 100 code/

echo "Running Flake8 linting..."
flake8 code/

echo "All linting and formatting checks passed."
