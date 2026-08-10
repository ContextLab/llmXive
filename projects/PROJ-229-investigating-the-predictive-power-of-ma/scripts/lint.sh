#!/bin/bash
# Linting and formatting check script for T003

set -e

echo "Running Black (format check)..."
black --check --diff code/ tests/ || {
    echo "ERROR: Black check failed. Run 'black code/ tests/' to fix formatting."
    exit 1
}

echo "Running isort (import sorting check)..."
isort --check-only --diff code/ tests/ || {
    echo "ERROR: isort check failed. Run 'isort code/ tests/' to fix imports."
    exit 1
}

echo "Running flake8 (linting)..."
flake8 code/ tests/ || {
    echo "ERROR: flake8 found issues."
    exit 1
}

echo "All linting and formatting checks passed!"
