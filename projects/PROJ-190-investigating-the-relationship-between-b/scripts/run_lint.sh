#!/bin/bash
# Run linting checks on the project

set -e

echo "Running ruff linting..."
ruff check code/ tests/ || {
    echo "Linting failed. Run 'ruff check --fix code/ tests/' to auto-fix."
    exit 1
}

echo "Linting passed."
