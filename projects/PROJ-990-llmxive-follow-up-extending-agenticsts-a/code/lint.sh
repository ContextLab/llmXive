#!/bin/bash
# Run Ruff linter on code/ and tests/
# This script checks for syntax errors, style violations, and potential bugs.

set -e

echo "Running Ruff linter..."
ruff check code/ tests/

echo "Linting complete."
