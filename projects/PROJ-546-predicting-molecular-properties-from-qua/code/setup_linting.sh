#!/bin/bash
# Script to initialize linting and formatting tools for the project.
# This script installs ruff and black, then runs a format check and lint check.

set -e

echo "Installing linting and formatting tools..."
pip install -r code/requirements.txt

echo "Running Black format check (dry-run)..."
black --check code/ tests/ || (
    echo "Formatting issues detected. Run 'black code/ tests/' to fix automatically."
    exit 1
)

echo "Running Ruff lint check..."
ruff check code/ tests/ || (
    echo "Linting errors detected. Run 'ruff check --fix code/ tests/' to attempt automatic fixes."
    exit 1
)

echo "Linting and formatting checks passed."
