#!/bin/bash
# Setup script for PROJ-525
# Creates necessary directories and installs dependencies

set -e

echo "Setting up project structure..."

# Create directories if they don't exist
mkdir -p code/utils
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/logs
mkdir -p reports
mkdir -p tests/unit

# Create .gitkeep files
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch data/logs/.gitkeep
touch reports/.gitkeep

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Run 'source venv/bin/activate' to use the environment."