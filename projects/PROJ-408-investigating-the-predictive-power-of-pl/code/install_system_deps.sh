#!/bin/bash
# install_system_deps.sh
# Installs system binaries required for phylogenetic analysis: mafft and fasttree.
# Verifies installation by checking if binaries are in PATH.
# Exits with non-zero status if installation or verification fails.

set -e  # Exit immediately if a command exits with a non-zero status

echo "=== Starting System Dependency Installation ==="

# Update package lists
echo "Updating package lists..."
apt-get update -qq

# Install mafft and fasttree
echo "Installing mafft and fasttree..."
apt-get install -y -qq mafft fasttree

# Verify installation
echo "Verifying installation..."

# Check mafft
if ! command -v mafft &> /dev/null; then
    echo "ERROR: mafft binary not found in PATH after installation."
    exit 1
fi
echo "SUCCESS: mafft found at $(which mafft)"
echo "mafft version info:"
mafft --version || true  # Some versions might not support --version, ignore error

# Check fasttree
if ! command -v FastTree &> /dev/null; then
    echo "ERROR: FastTree binary not found in PATH after installation."
    exit 1
fi
echo "SUCCESS: FastTree found at $(which FastTree)"
echo "FastTree version info:"
FastTree -version || true  # FastTree prints version to stderr on -version

echo "=== System Dependency Installation Complete ==="
echo "Both mafft and FastTree are installed and accessible in PATH."
