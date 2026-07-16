#!/usr/bin/env bash
# Script to format code and run linting checks for the project.
# Prerequisites: ruff and black must be installed (pip install -e ".[dev]")

set -e

echo "Running formatter (black)..."
black code/

echo "Running linter (ruff)..."
ruff check code/

echo "Format and lint check complete."
