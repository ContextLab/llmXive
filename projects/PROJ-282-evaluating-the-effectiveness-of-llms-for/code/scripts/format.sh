#!/bin/bash
set -e

echo "Running formatter (black) and ruff format..."
black .
ruff format .

echo "Formatting complete."
