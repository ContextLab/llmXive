#!/bin/bash
# Script to verify linting and formatting tools are configured and functional

set -e

echo "Checking linting and formatting configuration..."

# Check for required config files
if [ ! -f ".flake8" ]; then
    echo "Error: .flake8 configuration file not found."
    exit 1
fi

if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found."
    exit 1
fi

if [ ! -f ".pre-commit-config.yaml" ]; then
    echo "Error: .pre-commit-config.yaml not found."
    exit 1
fi

# Verify tools are installed
if ! command -v flake8 &> /dev/null; then
    echo "Warning: flake8 not found in PATH. Attempting to install dev dependencies..."
    pip install -e ".[dev]" || {
        echo "Error: Failed to install dev dependencies. Please install flake8 manually."
        exit 1
    }
fi

if ! command -v black &> /dev/null; then
    echo "Warning: black not found in PATH. Attempting to install dev dependencies..."
    pip install -e ".[dev]" || {
        echo "Error: Failed to install dev dependencies. Please install black manually."
        exit 1
    }
fi

if ! command -v isort &> /dev/null; then
    echo "Warning: isort not found in PATH. Attempting to install dev dependencies..."
    pip install -e ".[dev]" || {
        echo "Error: Failed to install dev dependencies. Please install isort manually."
        exit 1
    }
fi

# Run linting check (dry run)
echo "Running flake8 check..."
flake8 --version
flake8 --max-line-length=120 code/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics || true

# Run formatting check (dry run)
echo "Running black check..."
black --version
black --check --line-length=120 code/ tests/ || true

# Run isort check
echo "Running isort check..."
isort --check-only --profile=black --line-length=120 code/ tests/ || true

echo "Linting and formatting configuration verified successfully."