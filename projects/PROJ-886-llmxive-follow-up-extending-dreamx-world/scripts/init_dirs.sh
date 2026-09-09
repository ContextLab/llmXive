#!/bin/bash
# T001a: Initialize Project Structure Script
# Creates the full nested directory tree for PROJ-886-llmxive-follow-up-extending-dreamx-world
# Run from repository root.

set -e

PROJECT_ROOT="projects/PROJ-886-llmxive-follow-up-extending-dreamx-world"

echo "Initializing project structure at: $PROJECT_ROOT"

# Create base project directory
mkdir -p "$PROJECT_ROOT"

# Create data directories
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/derived"
mkdir -p "$PROJECT_ROOT/data/derived/videos"

# Create code directories
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/code/models"
mkdir -p "$PROJECT_ROOT/code/pipeline"
mkdir -p "$PROJECT_ROOT/code/analysis"
mkdir -p "$PROJECT_ROOT/code/utils"

# Create test directories
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"

# Create support directories
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/config"

# Create scripts directory for this task
mkdir -p "$PROJECT_ROOT/scripts"

echo "Project directory structure created successfully."
echo "Directories created:"
find "$PROJECT_ROOT" -type d | sort