#!/bin/bash
set -e

echo "Running flake8..."
flake8 code/

echo "Running pylint..."
pylint code/

echo "Linting complete."
