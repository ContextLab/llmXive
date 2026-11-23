#!/bin/bash
# Project Initialization Script for PROJ-336
# Creates the required directory structure and placeholder files.

set -e

echo "Initializing project structure for PROJ-336..."

# Define root directories
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create directories
mkdir -p "$ROOT_DIR/src"
mkdir -p "$ROOT_DIR/src/data"
mkdir -p "$ROOT_DIR/src/utils"
mkdir -p "$ROOT_DIR/src/analysis"
mkdir -p "$ROOT_DIR/src/viz"
mkdir -p "$ROOT_DIR/tests"
mkdir -p "$ROOT_DIR/tests/unit"
mkdir -p "$ROOT_DIR/tests/integration"
mkdir -p "$ROOT_DIR/data"
mkdir -p "$ROOT_DIR/results"
mkdir -p "$ROOT_DIR/specs"

# Create __init__.py files
touch "$ROOT_DIR/src/__init__.py"
touch "$ROOT_DIR/tests/__init__.py"

# Create .gitkeep files for data/results to ensure they are tracked
touch "$ROOT_DIR/data/.gitkeep"
touch "$ROOT_DIR/results/.gitkeep"

echo "Project structure created successfully."
echo "Directories created:"
find "$ROOT_DIR" -type d -maxdepth 2 | grep -E "(src|tests|data|results)" | sort
