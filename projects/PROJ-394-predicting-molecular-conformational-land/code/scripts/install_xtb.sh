#!/bin/bash
#
# install_xtb.sh
# Installs the GFN2-xTB (xtb) binary library required for energy calculations.
#
# Prerequisites:
#   - Option 1 (Preferred): conda/mamba installed and active
#   - Option 2: apt-get (Debian/Ubuntu) for system installation
#
# This script does NOT install via pip as xtb is a C++ binary.
#

set -e

echo "=== Installing GFN2-xTB (xtb) ==="

# Check for conda
if command -v conda &> /dev/null; then
    echo "Detected conda. Installing xtb via conda-forge..."
    conda install -c conda-forge xtb -y
    echo "xtb installed via conda."
    exit 0
fi

# Check for mamba
if command -v mamba &> /dev/null; then
    echo "Detected mamba. Installing xtb via conda-forge..."
    mamba install -c conda-forge xtb -y
    echo "xtb installed via mamba."
    exit 0
fi

# Fallback to apt (Debian/Ubuntu)
if command -v apt-get &> /dev/null; then
    echo "Conda not found. Attempting system installation via apt-get..."
    # Update package list
    sudo apt-get update -qq
    # Install xtb (package name may vary by distro, usually 'xtb' or 'libxtb-dev')
    # Note: On some systems, the binary might be in a different package or not available in default repos.
    # If 'xtb' is not found, users may need to add a PPA or build from source.
    if sudo apt-get install -y xtb; then
        echo "xtb installed via apt-get."
        exit 0
    else
        echo "ERROR: Could not install xtb via apt-get. Package 'xtb' not found in default repositories."
        echo "Please install xtb manually via conda-forge or build from source: https://xtb-docs.readthedocs.io/"
        exit 1
    fi
fi

echo "ERROR: No supported package manager (conda, mamba, apt-get) found."
echo "Please install xtb manually. See: https://xtb-docs.readthedocs.io/en/latest/installation.html"
exit 1
