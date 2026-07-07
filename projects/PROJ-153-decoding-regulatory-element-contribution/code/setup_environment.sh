#!/bin/bash
set -euo pipefail

# Script to initialize the Conda environment for the Yeast CRE Analysis project.
# This script reads environment.yml and creates the environment 'yeast-cre-analysis'.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/environment.yml"

echo "=== Yeast CRE Analysis Environment Setup ==="

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: environment.yml not found at $ENV_FILE"
    exit 1
fi

echo "Checking conda availability..."
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed or not in PATH."
    echo "Please install Miniconda/Anaconda and try again."
    exit 1
fi

ENV_NAME="yeast-cre-analysis"

echo "Creating/Updating Conda environment: $ENV_NAME"
echo "Using configuration: $ENV_FILE"

# Create or update the environment
# --yes to skip confirmation
# --file to use the yaml definition
conda env create --force --file "$ENV_FILE" --quiet

if [[ $? -eq 0 ]]; then
    echo "SUCCESS: Environment '$ENV_NAME' created successfully."
    echo ""
    echo "To activate this environment, run:"
    echo "  conda activate $ENV_NAME"
    echo ""
    echo "To verify installation, run:"
    echo "  conda activate $ENV_NAME && fastp --version && bowtie2 --version && macs2 --version"
else
    echo "ERROR: Failed to create conda environment."
    exit 1
fi