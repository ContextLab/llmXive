#!/bin/bash
set -e

echo "Running flake8..."
flake8 code/

echo "Running ruff check..."
ruff check code/

echo "Linting passed."
