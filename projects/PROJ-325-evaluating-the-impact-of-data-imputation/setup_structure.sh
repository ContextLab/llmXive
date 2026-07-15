#!/bin/bash
# Script to initialize the project directory structure for llmXive research pipeline.
# This script creates the required directories as per the implementation plan.

set -e

echo "Creating project directory structure..."

# Core directories
mkdir -p code
mkdir -p tests
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/contract

# Data directories
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/external
mkdir -p data/interim

# State and Specs
mkdir -p state
mkdir -p specs
mkdir -p specs/contracts
mkdir -p specs/001-evaluating-imputation-impact

# Figures and Reports
mkdir -p figures
mkdir -p reports

# Initialize Python package markers
touch code/__init__.py
touch tests/__init__.py

echo "Project structure created successfully."
echo "Directories:"
find . -type d -not -path "./.*" | sort
