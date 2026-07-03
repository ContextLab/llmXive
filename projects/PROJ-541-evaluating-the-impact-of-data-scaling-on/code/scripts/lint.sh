#!/bin/bash
set -e
echo "Running ruff linter..."
ruff check code/
echo "Linting complete."
