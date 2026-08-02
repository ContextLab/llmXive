#!/bin/bash
# Setup script for llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts
# Project: PROJ-881-llmxive-follow-up-extending-efficientrol
#
# This script creates the complete directory structure required for the project.
# Run from the project root directory.

set -e  # Exit immediately if a command exits with a non-zero status

PROJECT_ROOT="projects/PROJ-881-llmxive-follow-up-extending-efficientrol"

echo "Creating directory structure for $PROJECT_ROOT..."

# Create root project directories
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/docs"
mkdir -p "$PROJECT_ROOT/scripts"
mkdir -p "$PROJECT_ROOT/results"
mkdir -p "$PROJECT_ROOT/specs/001-entropy-validity-prediction/contracts"

# Create subdirectories under code/
mkdir -p "$PROJECT_ROOT/code/src"
mkdir -p "$PROJECT_ROOT/code/data/raw"
mkdir -p "$PROJECT_ROOT/code/data/processed"
mkdir -p "$PROJECT_ROOT/code/artifacts"
mkdir -p "$PROJECT_ROOT/code/state"

# Create additional standard subdirectories
mkdir -p "$PROJECT_ROOT/code/src/utils"
mkdir -p "$PROJECT_ROOT/code/src/data"
mkdir -p "$PROJECT_ROOT/code/src/generation"
mkdir -p "$PROJECT_ROOT/code/src/analysis"
mkdir -p "$PROJECT_ROOT/code/tests/unit"
mkdir -p "$PROJECT_ROOT/code/tests/integration"
mkdir -p "$PROJECT_ROOT/code/tests/contract"
mkdir -p "$PROJECT_ROOT/code/logs"

echo "Directory structure created successfully."
echo "All paths:"
find "$PROJECT_ROOT" -type d | sort