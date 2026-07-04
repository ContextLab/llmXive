#!/bin/bash
set -e
echo "Running Black..."
black code/
echo "Running Isort..."
isort code/
echo "Formatting complete."