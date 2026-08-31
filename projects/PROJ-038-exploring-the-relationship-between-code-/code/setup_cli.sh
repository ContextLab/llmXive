#!/bin/bash
# setup_cli.sh
# Installs Defects4j CLI dependencies (OpenJDK 17) and PMD (v7.0.0)
# to support Cyclomatic Complexity metric extraction.
#
# Requirements:
# - Apt package manager (Debian/Ubuntu based)
# - Root/sudo privileges
#
# Prerequisites:
# - T000a (External Governance Verification) must have passed.
# - T001a (Directory Structure) must exist.

set -e

echo ">>> [T002c] Starting CLI Tool Setup (Defects4j & PMD)..."

# Update package lists
echo ">>> Updating apt package lists..."
apt-get update

# Install OpenJDK 17 (pinned version for reproducibility)
# Defects4j requires Java 8+; 17 is selected for modern compatibility.
echo ">>> Installing OpenJDK 17..."
apt-get install -y openjdk-17-jdk=17.0.9+1

# Verify Java installation
echo ">>> Verifying Java installation..."
java -version

# Install PMD (pinned to 7.0.0 as per spec)
# Note: 'pmd-bin' is the package name in standard Debian/Ubuntu repos for PMD.
# If the specific version 7.0.0 is not in the default repo, the install may fail.
# The task requires exact versioning for reproducibility.
echo ">>> Installing PMD 7.0.0..."
apt-get install -y pmd-bin=7.0.0

# Verification steps
echo ">>> Verifying PMD installation..."
if command -v pmd &> /dev/null; then
    PMD_VERSION=$(pmd --version)
    echo "PMD Version: $PMD_VERSION"
else
    echo "ERROR: PMD command not found after installation."
    exit 1
fi

# Note: 'defects4j' CLI is typically installed via Perl CPAN or a specific script
# after the Java environment is ready. This script ensures the *prerequisites*
# (Java and PMD) are met as requested by the task description.
# The Defects4j client itself is usually invoked via `defects4j` if the PATH is set,
# or via the Perl script. We verify the environment is ready for it.
echo ">>> Environment ready for Defects4j and PMD usage."
echo ">>> [T002c] Setup complete."