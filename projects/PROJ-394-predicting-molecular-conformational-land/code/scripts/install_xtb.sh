#!/bin/bash
# Script to install xtb via conda-forge or system package manager
# xtb is a C++ binary and cannot be installed via pip.

set -e

echo "Attempting to install xtb..."

# Try conda first (preferred)
if command -v conda &> /dev/null; then
    echo "Conda detected. Installing xtb from conda-forge..."
    conda install -c conda-forge xtb -y
    echo "xtb installed successfully via conda."
    exit 0
fi

# Try apt (Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    echo "Apt detected. Installing xtb via apt..."
    sudo apt-get update
    sudo apt-get install -y xtb
    echo "xtb installed successfully via apt."
    exit 0
fi

# Try brew (macOS)
if command -v brew &> /dev/null; then
    echo "Brew detected. Installing xtb via brew..."
    brew install xtb
    echo "xtb installed successfully via brew."
    exit 0
fi

echo "ERROR: Could not find a suitable package manager (conda, apt, brew) to install xtb."
echo "Please install xtb manually from https://xtb-docs.readthedocs.io/"
exit 1