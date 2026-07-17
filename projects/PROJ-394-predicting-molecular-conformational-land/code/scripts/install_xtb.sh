#!/bin/bash
# Install xtb (GFN2-xTB) via conda-forge (preferred) or system package manager.
# This script is referenced in requirements.txt and plan.md.
#
# Usage: bash code/scripts/install_xtb.sh

set -e

if command -v conda &> /dev/null; then
    echo "Installing xtb via conda-forge..."
    conda install -y -c conda-forge xtb
    echo "xtb installation complete."
elif command -v apt-get &> /dev/null; then
    echo "Installing xtb via apt-get..."
    sudo apt-get update
    sudo apt-get install -y xtb
    echo "xtb installation complete."
elif command -v brew &> /dev/null; then
    echo "Installing xtb via Homebrew..."
    brew install xtb
    echo "xtb installation complete."
else
    echo "ERROR: No supported package manager found (conda, apt, brew)."
    echo "Please install xtb manually from: https://xtb-docs.readthedocs.io/"
    exit 1
fi
