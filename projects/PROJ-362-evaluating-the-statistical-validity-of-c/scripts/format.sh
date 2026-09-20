#!/bin/bash
# Format script for the project
# Runs black (formatter) and ruff (auto-fix)

set -e

echo "Running Black formatter..."
black .

echo "Running Ruff auto-fix..."
ruff check --fix .

echo "Formatting complete."