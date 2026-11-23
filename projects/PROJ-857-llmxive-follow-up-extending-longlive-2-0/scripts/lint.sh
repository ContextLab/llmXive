#!/bin/bash
# Lint code with Flake8
set -e

echo "Running Flake8..."
flake8 code/ tests/

echo "Linting complete."
