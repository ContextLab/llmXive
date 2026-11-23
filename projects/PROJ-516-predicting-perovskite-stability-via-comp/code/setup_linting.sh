#!/bin/bash
# Setup script to initialize linting and formatting tools for the project.
# This script should be run after installing dependencies (requirements.txt).

set -e

echo "=== Configuring Linting and Formatting Tools ==="

# Verify tools are installed
echo "Checking tool availability..."
command -v black >/dev/null 2>&1 || { echo "Error: black is not installed. Run 'pip install -r requirements.txt'"; exit 1; }
command -v isort >/dev/null 2>&1 || { echo "Error: isort is not installed. Run 'pip install -r requirements.txt'"; exit 1; }
command -v flake8 >/dev/null 2>&1 || { echo "Error: flake8 is not installed. Run 'pip install -r requirements.txt'"; exit 1; }
command -v pylint >/dev/null 2>&1 || { echo "Error: pylint is not installed. Run 'pip install -r requirements.txt'"; exit 1; }

echo "All tools found."

# Validate configuration files exist
if [ ! -f ".flake8" ]; then
    echo "Error: .flake8 configuration file missing."
    exit 1
fi
if [ ! -f "pylintrc" ]; then
    echo "Error: pylintrc configuration file missing."
    exit 1
fi
if [ ! -f ".isort.cfg" ]; then
    echo "Error: .isort.cfg configuration file missing."
    exit 1
fi
if [ ! -f ".black.toml" ]; then
    echo "Error: .black.toml configuration file missing."
    exit 1
fi

echo "Configuration files validated."

# Run a dry-run format check (black --check)
echo "Running Black format check (dry-run)..."
black --check --diff . || {
    echo "Warning: Code is not formatted according to Black standards."
    echo "Run 'black .' to fix formatting."
}

# Run a dry-run import sort check (isort --check)
echo "Running Isort import sort check (dry-run)..."
isort --check-only . || {
    echo "Warning: Imports are not sorted according to Isort standards."
    echo "Run 'isort .' to fix import sorting."
}

# Run a quick flake8 check on a small subset or just verify config
echo "Verifying Flake8 configuration..."
flake8 --version

echo "=== Linting and Formatting Setup Complete ==="
echo "To format code: black ."
echo "To sort imports: isort ."
echo "To run linter: flake8 ."
echo "To run full pylint: pylint code/"
echo "To run all checks: ./setup_linting.sh"