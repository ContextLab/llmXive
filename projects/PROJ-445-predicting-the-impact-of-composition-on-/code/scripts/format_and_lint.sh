#!/bin/bash
set -e

echo "Running Black formatter..."
black code/

echo "Running isort..."
isort code/

echo "Running Flake8..."
flake8 code/

echo "Linting and formatting complete."
