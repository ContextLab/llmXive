#!/usr/bin/env bash
set -e

echo "Installing Python dependencies..."
pip install -r code/requirements.txt

echo "Installing R dependencies..."
Rscript code/R/install_packages.R

echo "Verifying R dependencies..."
Rscript code/R/verify_requirements.R