#!/bin/bash
# Setup script for PROJ-843-llmxive-follow-up-extending-latent-spati
# Creates the required directory structure and initializes the project

set -e

PROJECT_ROOT="projects/PROJ-843-llmxive-follow-up-extending-latent-spati"

echo "Creating project directory structure for llmXive..."

# Create main project directory
mkdir -p "$PROJECT_ROOT"

# Create code directories
mkdir -p "$PROJECT_ROOT/code/utils"
mkdir -p "$PROJECT_ROOT/code/data"
mkdir -p "$PROJECT_ROOT/code/geometry"
mkdir -p "$PROJECT_ROOT/code/eval"

# Create data directories
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/processed"
mkdir -p "$PROJECT_ROOT/data/stratified"
mkdir -p "$PROJECT_ROOT/data/features"
mkdir -p "$PROJECT_ROOT/data/results"

# Create tests directories
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"

# Create specs directory if not exists
mkdir -p "$PROJECT_ROOT/specs"

# Create __init__.py files to make directories packages
touch "$PROJECT_ROOT/code/__init__.py"
touch "$PROJECT_ROOT/code/utils/__init__.py"
touch "$PROJECT_ROOT/code/data/__init__.py"
touch "$PROJECT_ROOT/code/geometry/__init__.py"
touch "$PROJECT_ROOT/code/eval/__init__.py"
touch "$PROJECT_ROOT/data/__init__.py"
touch "$PROJECT_ROOT/tests/__init__.py"
touch "$PROJECT_ROOT/tests/unit/__init__.py"
touch "$PROJECT_ROOT/tests/integration/__init__.py"

echo "Directory structure created successfully."
echo "Project root: $PROJECT_ROOT"
echo "Directories:"
find "$PROJECT_ROOT" -type d | sort