#!/bin/bash
# Shell script to run linting and formatting checks
# Usage: ./code/setup_linting_config.sh

set -e

echo "Running Ruff linting..."
ruff check .

echo "Running Black formatting check..."
black --check .

echo "All checks passed!"