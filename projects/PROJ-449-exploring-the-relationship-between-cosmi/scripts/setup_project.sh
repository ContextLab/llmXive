#!/bin/bash
set -e

echo "Creating project directory structure..."
mkdir -p code/data
mkdir -p code/utils
mkdir -p code/analysis
mkdir -p tests
mkdir -p data/raw
mkdir -p data/processed
mkdir -p figures

echo "Initializing Python virtual environment..."
python3 -m venv venv

echo "Activating environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Project structure created successfully."
echo "Run 'source venv/bin/activate' to start working."