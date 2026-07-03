#!/bin/bash
# Setup directories for the molecular reactivity project

set -e

echo "Creating project directory structure..."

# Data directories
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/models

# Source directories
mkdir -p src/data
mkdir -p src/modeling
mkdir -p src/utils

# Test directories
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/contract

# Scripts and state
mkdir -p scripts
mkdir -p state/projects

# Figures and reports
mkdir -p figures

echo "Directory structure created successfully."
ls -R
