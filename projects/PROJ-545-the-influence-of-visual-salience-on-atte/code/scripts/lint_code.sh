#!/bin/bash
# Script to lint the codebase using Ruff.

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting complete."
