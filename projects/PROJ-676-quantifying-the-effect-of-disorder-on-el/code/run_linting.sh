#!/bin/bash
# Run linting tools on the code directory

set -e

echo "Running flake8..."
flake8 code/

echo "Running black --check..."
black --check code/

echo "Linting completed successfully."
