#!/bin/bash
# Run flake8 linting on the codebase
set -e
echo "Running flake8..."
flake8 code/
echo "Linting complete."
