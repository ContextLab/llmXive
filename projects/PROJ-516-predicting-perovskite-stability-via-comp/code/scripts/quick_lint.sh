#!/bin/bash
# Quick linting check without full reformat
# Usage: ./scripts/quick_lint.sh

set -e

echo "Running quick Flake8 check..."
flake8 code/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

echo "Running quick Pylint check (errors only)..."
pylint code/ tests/ --errors-only

echo "Quick linting passed."