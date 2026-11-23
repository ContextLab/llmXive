#!/bin/bash
# Script to initialize the project structure
# Run from the project root directory

set -e

echo "Initializing project structure..."

# Create directories
mkdir -p code
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/artifacts
mkdir -p tests
mkdir -p state
mkdir -p specs

echo "Creating __init__.py files..."
touch code/__init__.py
touch tests/__init__.py
touch data/__init__.py
touch data/raw/__init__.py
touch data/processed/__init__.py
touch data/artifacts/__init__.py
touch state/__init__.py
touch specs/__init__.py

echo "Project structure initialized successfully."
ls -la