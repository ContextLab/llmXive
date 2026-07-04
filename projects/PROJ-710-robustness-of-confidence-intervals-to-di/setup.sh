#!/bin/bash
# Setup script to create the project directory structure
# This script ensures all required directories exist

PROJECT_DIR="projects/PROJ-710-robustness-of-confidence-intervals-to-di"

echo "Creating project directory structure for $PROJECT_DIR..."

# Create main directories
mkdir -p "$PROJECT_DIR/code/data"
mkdir -p "$PROJECT_DIR/code/analysis"
mkdir -p "$PROJECT_DIR/code/utils"
mkdir -p "$PROJECT_DIR/code/tests"
mkdir -p "$PROJECT_DIR/artifacts"

# Create __init__.py files to make directories Python packages
touch "$PROJECT_DIR/code/__init__.py"
touch "$PROJECT_DIR/code/data/__init__.py"
touch "$PROJECT_DIR/code/analysis/__init__.py"
touch "$PROJECT_DIR/code/utils/__init__.py"
touch "$PROJECT_DIR/code/tests/__init__.py"

echo "Directory structure created successfully."
echo "Project root: $PROJECT_DIR"
echo ""
echo "Directory tree:"
tree "$PROJECT_DIR" 2>/dev/null || find "$PROJECT_DIR" -type d | head -20
