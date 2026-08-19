#!/bin/bash
# Script to verify linting and formatting tools are installed and configured
set -e

echo "Checking for flake8..."
if ! command -v flake8 &> /dev/null; then
    echo "flake8 is not installed. Installing..."
    pip install flake8
fi

echo "Checking for black..."
if ! command -v black &> /dev/null; then
    echo "black is not installed. Installing..."
    pip install black
fi

echo "Linting configuration found:"
if [ -f ".flake8" ]; then
    echo "  - .flake8 (flake8 config)"
else
    echo "  WARNING: .flake8 not found"
fi

if [ -f "pyproject.toml" ]; then
    echo "  - pyproject.toml (black config)"
else
    echo "  WARNING: pyproject.toml not found"
fi

if [ -f "Makefile" ]; then
    echo "  - Makefile (lint/format targets)"
else
    echo "  WARNING: Makefile not found"
fi

echo "Linting and formatting tools are ready."