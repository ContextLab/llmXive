#!/bin/bash
set -e

echo "Running flake8..."
flake8 src/ tests/

echo "Linting complete."
