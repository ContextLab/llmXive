#!/bin/bash
# Run flake8 and black checks on the project
set -e

echo "Running flake8..."
flake8 code/ tests/ --config=.flake8

echo "Running black check..."
black --check code/ tests/ --config=pyproject.toml

echo "Linting and formatting checks passed."
