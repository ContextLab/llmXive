#!/bin/bash
set -e

echo "Running flake8..."
flake8 code/ tests/ --config=.flake8

echo "Running isort check..."
isort --check-only --diff code/ tests/

echo "Running black check..."
black --check --diff code/ tests/

echo "Linting passed."
