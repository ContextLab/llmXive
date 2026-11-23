#!/bin/bash
# Setup script for system dependencies (minimap2 and bcftools)
# This script should be run on the host machine if not using Docker/CI
# It assumes a Debian/Ubuntu based system.

set -e

echo "Updating package lists..."
sudo apt-get update

echo "Installing minimap2 and bcftools..."
sudo apt-get install -y minimap2 bcftools

echo "Verifying installations..."
if command -v minimap2 &> /dev/null; then
    echo "minimap2 installed successfully:"
    minimap2 --version
else
    echo "ERROR: minimap2 installation failed."
    exit 1
fi

if command -v bcftools &> /dev/null; then
    echo "bcftools installed successfully:"
    bcftools --version
else
    echo "ERROR: bcftools installation failed."
    exit 1
fi

echo "System dependencies setup complete."