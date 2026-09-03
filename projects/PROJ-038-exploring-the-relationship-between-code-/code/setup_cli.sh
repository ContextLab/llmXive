#!/bin/bash
# setup_cli.sh
# Installs system-level dependencies required for the Defects4J CLI and PMD static analysis tool.
# This script must be run with sudo privileges.
#
# Prerequisites:
# - A Debian/Ubuntu-based environment
# - Internet access for package retrieval
#
# Dependencies installed:
# - openjdk-17-jdk (Pinned to 17.0.9+1 for reproducibility)
# - pmd-bin (Pinned to 7.0.0 for reproducibility)
#
# Verification:
# - defects4j --version
# - pmd --version

set -euo pipefail

echo ">>> [T002c] Starting CLI tool installation (Defects4J & PMD)..."

# Update package lists
echo ">>> Updating apt package lists..."
sudo apt-get update

# Install OpenJDK 17 (Pinned version)
echo ">>> Installing OpenJDK 17 (pinned to 17.0.9+1)..."
sudo apt-get install -y openjdk-17-jdk=17.0.9+1

# Verify Java installation
if ! command -v java &> /dev/null; then
    echo "ERROR: Java installation failed."
    exit 1
fi
echo ">>> Java version check:"
java -version

# Install PMD (Pinned version)
# Note: pmd-bin is the package name in many Debian/Ubuntu repos for PMD 7.x
echo ">>> Installing PMD (pinned to 7.0.0)..."
sudo apt-get install -y pmd-bin=7.0.0

# Verify PMD installation
if ! command -v pmd &> /dev/null; then
    echo "ERROR: PMD installation failed."
    exit 1
fi
echo ">>> PMD version check:"
pmd --version

# Note: Defects4J CLI is typically installed via git clone and a setup script.
# This task specifically requested the installation of the *tools* (JDK and PMD)
# via apt. If 'defects4j' is not in PATH, it implies the Defects4J repository
# itself needs to be cloned and sourced separately (often handled in T004b or T013).
# However, we verify if it exists as requested.
if command -v defects4j &> /dev/null; then
    echo ">>> Defects4J CLI found:"
    defects4j --version
else
    echo ">>> WARNING: 'defects4j' command not found in PATH."
    echo ">>> This is expected if the Defects4J repository has not yet been cloned and sourced."
    echo ">>> Ensure Defects4J is installed separately (e.g., via git clone https://github.com/rjust/defects4j.git) and sourced."
fi

echo ">>> [T002c] CLI tool installation complete."
echo ">>> Please ensure Defects4J repository is cloned and sourced before running the pipeline."
exit 0