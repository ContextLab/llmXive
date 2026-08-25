#!/bin/bash
# setup_system_deps.sh
# Installs system binaries required for phylogenetic analysis: mafft and fasttree.
# This script is intended to run on Debian/Ubuntu-based runners.

set -e

echo ">>> Installing system dependencies for phylogenetic analysis..."

# Update package lists
apt-get update -qq

# Install MAFFT (Multiple Alignment using Fast Fourier Transform)
echo ">>> Installing mafft..."
if ! apt-get install -y -qq mafft; then
    echo "ERROR: Failed to install mafft" >&2
    exit 1
fi

# Install FastTree (Approximate Maximum-Likelihood Trees)
# Note: On some systems it might be named 'fasttree' or 'fasttree2'
echo ">>> Installing fasttree..."
if ! apt-get install -y -qq fasttree; then
    # Fallback for systems where the package might be named differently or missing
    # Try to install from source if package manager fails, though apt-get is preferred
    echo "WARNING: apt-get install fasttree failed. Attempting to verify if it exists or install via alternative..."
    if ! command -v FastTree &> /dev/null; then
        echo "ERROR: Could not install fasttree via apt-get and FastTree binary not found in PATH." >&2
        echo "Note: On some Ubuntu versions, the package is 'fasttree' but the binary is 'FastTree' (capital F)." >&2
        echo "If 'apt-get install fasttree' failed, you may need to build from source or find the correct package name." >&2
        exit 1
    fi
fi

echo ">>> Verifying binaries are in PATH..."

# Verify MAFFT
if command -v mafft &> /dev/null; then
    MAFFT_VERSION=$(mafft --version 2>&1 | head -n 1 || echo "unknown")
    echo "SUCCESS: mafft found ($MAFFT_VERSION)"
else
    echo "ERROR: mafft not found in PATH after installation." >&2
    exit 1
fi

# Verify FastTree (checking for common binary names: FastTree, fasttree)
FASTTREE_FOUND=false
for cmd in FastTree fasttree; do
    if command -v $cmd &> /dev/null; then
        FASTTREE_VERSION=$($cmd --version 2>&1 | head -n 1 || echo "unknown")
        echo "SUCCESS: $cmd found ($FASTTREE_VERSION)"
        FASTTREE_FOUND=true
        break
    fi
done

if [ "$FASTTREE_FOUND" = false ]; then
    echo "ERROR: Neither FastTree nor fasttree found in PATH after installation." >&2
    exit 1
fi

echo ">>> System dependencies installed and verified successfully."
