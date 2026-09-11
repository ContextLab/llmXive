#!/bin/bash
set -e

echo "Running flake8 linting..."
flake8 code/

echo "Running black check..."
black --check code/

echo "Running isort check..."
isort --check-only code/

echo "All linting checks passed!"
