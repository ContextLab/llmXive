#!/bin/bash
# Script to run Black formatting and Ruff linting on the project

set -e

echo "Running Black formatter..."
black code/

echo "Running Ruff linter..."
ruff check code/

echo "Formatting and linting complete."