#!/bin/bash
set -e

echo "Running Ruff Fix..."
ruff check --fix .

echo "Running Black Formatter..."
black .

echo "Formatting applied successfully."