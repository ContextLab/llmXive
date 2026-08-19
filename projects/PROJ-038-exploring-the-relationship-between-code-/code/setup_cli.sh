#!/bin/bash
# setup_cli.sh - Install and verify Defects4J and PMD CLI tools
# This script ensures the required system tools are installed and executable
# before proceeding with the research pipeline.

set -e  # Exit immediately if a command exits with a non-zero status

echo "=== llmXive Pipeline Setup: CLI Tools Verification ==="

# Function to check if a command is available and executable
verify_binary() {
    local binary_name=$1
    local version_flag=$2
    local install_instruction=$3

    echo "Checking for ${binary_name}..."

    if ! command -v ${binary_name} &> /dev/null; then
        echo "ERROR: ${binary_name} is not installed or not in PATH."
        echo "Please install it using: ${install_instruction}"
        exit 1
    fi

    # Verify the binary is executable
    if [ ! -x "$(command -v ${binary_name})" ]; then
        echo "ERROR: ${binary_name} found but is not executable."
        echo "Please fix permissions: chmod +x $(which ${binary_name})"
        exit 1
    fi

    # Run version check to ensure it's a valid binary
    echo "Verifying ${binary_name} version..."
    ${binary_name} ${version_flag} || {
        echo "ERROR: ${binary_name} ${version_flag} failed."
        echo "The binary exists but is not functioning correctly."
        exit 1
    }

    echo "✓ ${binary_name} is installed and executable."
    echo ""
}

# Verify Defects4J
# Note: Defects4J CLI is usually invoked via 'defects4j'
verify_binary "defects4j" "--version" "See T002c instructions for Defects4J installation (wget/apt)."

# Verify PMD
# Note: PMD CLI is usually invoked via 'pmd'
verify_binary "pmd" "-version" "See T002d instructions for PMD installation (wget/apt)."

echo "=== All CLI tools verified successfully. ==="
echo "The pipeline can now proceed with data ingestion and metric extraction."