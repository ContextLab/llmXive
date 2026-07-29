#!/bin/bash
# Setup script for PROJ-349-predicting-the-impact-of-ball-milling-on
# Creates the required directory structure

set -e

echo "Setting up project directory structure..."

# Core directories
mkdir -p src
mkdir -p tests

# Data directories
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/splits

# Results and contracts
mkdir -p results
mkdir -p contracts

# CI/CD
mkdir -p .github/workflows

# Configuration and documentation
mkdir -p docs
mkdir -p scripts

# Create placeholder files to ensure directories are tracked by git
touch src/.gitkeep
touch tests/.gitkeep
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/splits/.gitkeep
touch results/.gitkeep
touch contracts/.gitkeep
touch .github/workflows/.gitkeep
touch docs/.gitkeep
touch scripts/.gitkeep

echo "Directory structure created successfully."
echo "Directories created:"
echo "  - src/"
echo "  - tests/"
echo "  - data/raw/"
echo "  - data/processed/"
echo "  - data/splits/"
echo "  - results/"
echo "  - contracts/"
echo "  - .github/workflows/"
echo "  - docs/"
echo "  - scripts/"