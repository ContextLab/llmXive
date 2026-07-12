#!/bin/bash
# Script to run flake8 linting

set -e

echo "Running flake8..."
python -m flake8 code/ tests/

echo "Linting complete."
