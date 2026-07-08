#!/bin/bash
# init_structure.sh - Automate directory creation and initial file scaffolding for PROJ-431
# This script creates the standard project structure and initializes empty placeholder files
# to ensure the project is ready for development.

set -e  # Exit immediately if a command exits with a non-zero status

# Define the project root (assumes script is run from project root)
PROJECT_ROOT="."

echo "🚀 Initializing project structure for PROJ-431..."

# 1. Create Directory Structure
echo "📂 Creating directories..."
mkdir -p "${PROJECT_ROOT}/data/raw"
mkdir -p "${PROJECT_ROOT}/data/processed"
mkdir -p "${PROJECT_ROOT}/results/models"
mkdir -p "${PROJECT_ROOT}/results/reports"
mkdir -p "${PROJECT_ROOT}/results/plots"
mkdir -p "${PROJECT_ROOT}/code"
mkdir -p "${PROJECT_ROOT}/tests"
mkdir -p "${PROJECT_ROOT}/tests/unit"
mkdir -p "${PROJECT_ROOT}/tests/integration"
mkdir -p "${PROJECT_ROOT}/scripts"
mkdir -p "${PROJECT_ROOT}/docs"

# 2. Create Initial File Scaffolding (Empty or Minimal Content)
echo "📝 Creating initial files..."

# Code files (empty or with minimal imports to satisfy structure)
touch "${PROJECT_ROOT}/code/__init__.py"
touch "${PROJECT_ROOT}/code/cli.py"
touch "${PROJECT_ROOT}/code/entropy.py"
touch "${PROJECT_ROOT}/code/model.py"
touch "${PROJECT_ROOT}/code/utils.py"
touch "${PROJECT_ROOT}/code/viz.py"

# Test files
touch "${PROJECT_ROOT}/tests/__init__.py"
touch "${PROJECT_ROOT}/tests/unit/__init__.py"
touch "${PROJECT_ROOT}/tests/integration/__init__.py"

# Documentation
touch "${PROJECT_ROOT}/docs/research.md"
touch "${PROJECT_ROOT}/docs/data-model.md"
touch "${PROJECT_ROOT}/README.md"

# Configuration
touch "${PROJECT_ROOT}/code/requirements.txt"

# 3. Verify Structure
echo "✅ Verifying structure..."
if [ -d "${PROJECT_ROOT}/data/raw" ] && \
   [ -d "${PROJECT_ROOT}/data/processed" ] && \
   [ -d "${PROJECT_ROOT}/results/models" ] && \
   [ -d "${PROJECT_ROOT}/results/reports" ] && \
   [ -d "${PROJECT_ROOT}/results/plots" ] && \
   [ -d "${PROJECT_ROOT}/code" ] && \
   [ -d "${PROJECT_ROOT}/tests" ]; then
    echo "🎉 Project structure initialized successfully!"
    echo ""
    echo "Directory tree:"
    find . -type d -not -path "*/\.*" | sort | head -20
else
    echo "❌ Error: Directory creation failed."
    exit 1
fi