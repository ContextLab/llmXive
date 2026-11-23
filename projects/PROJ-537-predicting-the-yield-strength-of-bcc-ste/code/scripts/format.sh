#!/bin/bash
set -e

echo "Running black formatting..."
black code/

echo "Running isort formatting..."
isort code/

echo "All formatting checks passed!"