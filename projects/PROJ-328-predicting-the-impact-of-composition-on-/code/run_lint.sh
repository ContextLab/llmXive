#!/bin/bash
# Run linting and formatting checks for the solder hardness prediction project

set -e

echo "Running flake8 linting..."
flake8 code/

echo "Running black check (dry run)..."
black --check code/

echo "All linting and formatting checks passed!"
