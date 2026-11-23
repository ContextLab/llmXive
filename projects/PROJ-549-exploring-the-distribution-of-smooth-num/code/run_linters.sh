#!/bin/bash
# Script to run all linters and formatters, fixing issues where safe
# Usage: ./code/run_linters.sh

set -e

echo "Formatting code with Black..."
black --line-length 100 code/

echo "Linting with Flake8..."
flake8 --max-line-length=100 --ignore=E203,E266,W503 code/

echo "Linting with Pylint..."
pylint --max-line-length=100 --disable=C0114,C0115,C0116,R0903,W0511 code/

echo "Done."
