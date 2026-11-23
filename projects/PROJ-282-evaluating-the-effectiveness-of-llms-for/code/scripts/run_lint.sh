#!/bin/bash
set -e
echo "Running linting with ruff..."
cd "$(dirname "$0")/.."
ruff check code/src code/tests code/setup_project_structure.py
echo "Linting complete."
