#!/bin/bash
# Script to run flake8 linting on the codebase

set -e

echo "Running flake8 linting..."
flake8 code/

if [ $? -eq 0 ]; then
    echo "Linting passed!"
    exit 0
else
    echo "Linting failed!"
    exit 1
fi
