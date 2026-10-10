#!/bin/bash
set -e
echo "Establishing project directory structure..."
mkdir -p code/simulation code/analysis code/visualization code/reporting code/scripts
mkdir -p data/raw data/processed data/results
mkdir -p tests/unit tests/integration
echo "Project structure established successfully."
