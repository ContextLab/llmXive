##!/bin/bash
set -e

echo "Running Black Formatter..."
black .

echo "Running Ruff Fix..."
ruff check . --fix

echo "Formatting complete."