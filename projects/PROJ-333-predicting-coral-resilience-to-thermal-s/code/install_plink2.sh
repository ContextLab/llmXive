#!/bin/bash
set -e

# Install PLINK2 for the project
# This script handles the installation of PLINK2 via apt-get or conda-forge
# depending on the environment.

echo "Checking for PLINK2 installation..."

if command -v plink2 &> /dev/null; then
    echo "PLINK2 is already installed: $(plink2 --version)"
    exit 0
fi

# Try installing via apt-get (Debian/Ubuntu based systems)
if command -v apt-get &> /dev/null; then
    echo "Installing PLINK2 via apt-get..."
    sudo apt-get update
    sudo apt-get install -y plink2
    
    if command -v plink2 &> /dev/null; then
        echo "PLINK2 installed successfully via apt-get."
        plink2 --version
        exit 0
    fi
fi

# Try installing via conda (if conda is available)
if command -v conda &> /dev/null; then
    echo "Installing PLINK2 via conda-forge..."
    conda install -c bioconda plink2 -y
    
    if command -v plink2 &> /dev/null; then
        echo "PLINK2 installed successfully via conda."
        plink2 --version
        exit 0
    fi
fi

echo "ERROR: Could not install PLINK2. Please install it manually."
echo "Option 1 (apt-get): sudo apt-get install plink2"
echo "Option 2 (conda): conda install -c bioconda plink2"
exit 1
