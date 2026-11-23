#!/bin/bash
set -e

echo "Running Black format check..."
black --check --diff code/ tests/

echo "Running Flake8 linting..."
flake8 code/ tests/

echo "All linting and formatting checks passed."
