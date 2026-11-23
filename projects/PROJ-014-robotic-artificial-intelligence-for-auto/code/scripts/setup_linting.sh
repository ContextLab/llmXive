#!/bin/bash
# Setup script for linting and formatting tools
# This script ensures ruff and black are installed and configured

set -e

echo "Installing linting and formatting tools..."
pip install "ruff==0.1.6" "black==23.11.0"

echo "Linting and formatting tools configured."
echo "To run linter:   ruff check code/"
echo "To run formatter: black code/"
echo "To run both:     ruff check code/ && black code/"
