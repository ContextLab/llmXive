#!/bin/bash
set -e
echo "Running Flake8..."
flake8 code/
echo "Running Pylint..."
pylint code/
echo "Linting complete."
