#!/usr/bin/env bash
set -e

echo "Running flake8..."
flake8 code/ tests/

echo "Running black check..."
black --check code/ tests/

echo "Running isort check..."
isort --check-only --diff code/ tests/

echo "Linting passed."
