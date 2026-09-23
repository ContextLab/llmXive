#!/bin/bash
# Script to install and configure linting and formatting tools

set -e

echo "Installing linting and formatting tools..."
pip install flake8 black isort pytest-cov

echo "Verifying installation..."
flake8 --version
black --version
isort --version

echo "Linting and formatting tools installed successfully."
echo "Run 'make lint' to check code style."
echo "Run 'make format' to auto-format code."
echo "Run 'make test' to run tests."
