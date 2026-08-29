#!/bin/bash
set -e

echo "=== llmXive Project: Installing CLI Dependencies ==="
echo "Installing Defects4J CLI and PMD (Java Static Analysis Tool)..."

# Check for root/sudo privileges (required for apt)
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (sudo) to install system packages."
    exit 1
fi

# Update package lists
echo "[1/4] Updating package lists..."
apt-get update -qq

# Install Defects4J dependencies (git, wget, etc.) if not present
echo "[2/4] Installing Defects4J dependencies..."
apt-get install -y -qq git wget openjdk-11-jdk > /dev/null 2>&1 || true

# Install PMD (Java Static Analysis Tool) via apt
# Note: PMD is often available as 'pmd' or 'pmd-bin' in newer repos, 
# or we can download the specific version via wget if the repo version is too old.
# We will attempt apt first, then fallback to wget if needed to ensure a recent version.
echo "[3/4] Installing PMD..."
if ! command -v pmd &> /dev/null; then
    echo "  -> PMD not found in system path. Installing via apt..."
    apt-get install -y -qq pmd > /dev/null 2>&1 || {
        echo "  -> Apt install failed or package missing. Downloading PMD manually..."
        # Download PMD 7.0.0 (or latest stable)
        PMD_VERSION="7.0.0"
        PMD_URL="https://github.com/pmd/pmd/releases/download/pmd_releases/${PMD_VERSION}/pmd-${PMD_VERSION}.zip"
        wget -q -O /tmp/pmd.zip "$PMD_URL"
        unzip -q -o /tmp/pmd.zip -d /opt/
        ln -s /opt/pmd-${PMD_VERSION}/bin/pmd /usr/local/bin/pmd
        rm /tmp/pmd.zip
    }
fi

# Verify PMD
echo "  -> Verifying PMD installation..."
if command -v pmd &> /dev/null; then
    pmd_version=$(pmd --version 2>&1 || pmd -version 2>&1)
    echo "  -> PMD installed: $pmd_version"
else
    echo "  -> ERROR: PMD installation verification failed."
    exit 1
fi

# Install Defects4J CLI
# Defects4J is typically installed via a git clone and a setup script.
# We use the standard installation method for Defects4J v2.0+.
echo "[4/4] Installing Defects4J..."
DEFECTS4J_DIR="/opt/defects4j"

if [ -d "$DEFECTS4J_DIR" ]; then
    echo "  -> Defects4J directory already exists at $DEFECTS4J_DIR. Updating..."
    cd "$DEFECTS4J_DIR"
    git pull origin main
else
    echo "  -> Cloning Defects4J from GitHub..."
    mkdir -p /opt
    cd /opt
    git clone https://github.com/rjust/defects4j.git defects4j
    cd defects4j
    # Run the init script to setup the database and tools
    ./init.sh
fi

# Add Defects4J to PATH for the current session and ensure it's available
export DEFECTS4J_DIR
export PATH="$DEFECTS4J_DIR/bin:$PATH"

# Verify Defects4J
echo "  -> Verifying Defects4J installation..."
if command -v defects4j &> /dev/null; then
    defects4j_version=$(defects4j --version 2>&1)
    echo "  -> Defects4J installed: $defects4j_version"
else
    echo "  -> ERROR: Defects4J installation verification failed."
    echo "  -> Check if /opt/defects4j/bin/defects4j exists and is executable."
    exit 1
fi

echo ""
echo "=== Installation Complete ==="
echo "Defects4J Version: $defects4j_version"
echo "PMD Version: $pmd_version"
echo "Both tools are now available in the system PATH."
echo "Note: You may need to run 'export PATH=/opt/defects4j/bin:\$PATH' in your shell session."