#!/bin/bash
# init_conda_env.sh
# Initializes the Conda environment for the Yeast CRE Analysis project.
# This script reads environment.yml and creates/updates the 'yeast-cre-analysis' environment.

set -e  # Exit immediately if a command exits with a non-zero status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/environment.yml"

echo "=========================================="
echo "Initializing Conda Environment"
echo "=========================================="

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: environment.yml not found at $ENV_FILE"
    exit 1
fi

echo "Found environment definition: $ENV_FILE"

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "ERROR: Conda is not installed or not in PATH."
    echo "Please install Miniconda or Anaconda and try again."
    exit 1
fi

echo "Conda version: $(conda --version)"

# Create or update the environment
# --force creates the environment even if it already exists
echo "Creating/Updating environment 'yeast-cre-analysis'..."
conda env create -f "$ENV_FILE" --force

# Verify the environment was created
if conda env list | grep -q "yeast-cre-analysis"; then
    echo "SUCCESS: Environment 'yeast-cre-analysis' is ready."
    echo ""
    echo "To activate this environment, run:"
    echo "  conda activate yeast-cre-analysis"
    echo ""
    echo "To verify installation, run:"
    echo "  conda activate yeast-cre-analysis && fastp --version && bowtie2 --version"
else
    echo "ERROR: Failed to create environment 'yeast-cre-analysis'."
    exit 1
fi
