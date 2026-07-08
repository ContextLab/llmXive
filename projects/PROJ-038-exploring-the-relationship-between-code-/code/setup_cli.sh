#!/bin/bash
set -e

echo "=== llmXive Project Setup: Defects4J & PMD ==="
echo "This script installs and configures the Defects4J CLI and PMD static analysis tool."

# Check for root/sudo privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root (sudo)."
  exit 1
fi

# Update package lists
echo "[1/5] Updating package lists..."
apt-get update -qq

# Install dependencies for wget, git, and Java
echo "[2/5] Installing system dependencies (git, wget, openjdk-11-jdk)..."
apt-get install -y -qq git wget openjdk-11-jdk

# --- Install PMD ---
echo "[3/5] Installing PMD (Java static analysis tool)..."
PMD_VERSION="6.55.0"
PMD_URL="https://github.com/pmd/pmd/releases/download/pmd-releases-${PMD_VERSION}/pmd-bin-${PMD_VERSION}.tar.gz"
PMD_TEMP_DIR="/tmp/pmd-install"

mkdir -p ${PMD_TEMP_DIR}
cd ${PMD_TEMP_DIR}
wget -q ${PMD_URL} -O pmd-bin.tar.gz
tar -xzf pmd-bin.tar.gz --strip-components=1
mv pmd-bin-${PMD_VERSION} /opt/pmd
ln -sf /opt/pmd/bin/pmd /usr/local/bin/pmd

# Verify PMD
echo "Verifying PMD installation..."
if ! pmd --version; then
  echo "Error: PMD installation verification failed."
  exit 1
fi
echo "PMD installed successfully."

# --- Install Defects4J ---
echo "[4/5] Installing Defects4J CLI..."
D4J_VERSION="2.0.0"
D4J_URL="https://github.com/rjust/defects4j/releases/download/v${D4J_VERSION}/defects4j-v${D4J_VERSION}.tar.gz"
D4J_TEMP_DIR="/tmp/d4j-install"

mkdir -p ${D4J_TEMP_DIR}
cd ${D4J_TEMP_DIR}
wget -q ${D4J_URL} -O defects4j.tar.gz
tar -xzf defects4j.tar.gz --strip-components=1
mv defects4j-${D4J_VERSION} /opt/defects4j
ln -sf /opt/defects4j/bin/defects4j /usr/local/bin/defects4j

# Configure Defects4J environment variables (optional but recommended for stability)
# Note: Users should source this or add to .bashrc for persistent sessions,
# but the CLI binary is now in PATH.
echo "export D4J_HOME=/opt/defects4j" >> /etc/profile.d/defects4j.sh
echo "export PATH=\$PATH:/opt/defects4j/bin" >> /etc/profile.d/defects4j.sh

# Verify Defects4J
echo "Verifying Defects4J installation..."
if ! defects4j --version; then
  echo "Error: Defects4J installation verification failed."
  exit 1
fi
echo "Defects4J installed successfully."

# Cleanup
rm -rf ${PMD_TEMP_DIR} ${D4J_TEMP_DIR}

echo "[5/5] Setup complete."
echo "Tools available:"
pmd --version
defects4j --version
echo "=== Setup Finished ==="