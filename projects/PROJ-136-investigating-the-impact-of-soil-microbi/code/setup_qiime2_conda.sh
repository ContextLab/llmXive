#!/bin/bash
# Setup script to install QIIME 2 via Conda
# This script assumes conda (miniconda or anaconda) is already installed.
# QIIME 2 is NOT installed via pip per Constitution Principle I.

set -e

# Configuration
QIIME2_VERSION="2023.9"
ENV_NAME="qiime2-${QIIME2_VERSION}"

echo "================================================"
echo "Setting up QIIME 2 ${QIIME2_VERSION} environment"
echo "================================================"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda could not be found."
    echo "Please install Miniconda or Anaconda first:"
    echo "https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Update conda
echo "Updating conda..."
conda update -y -n base conda

# Create environment with QIIME 2
echo "Creating environment: ${ENV_NAME}"
conda create -y -n ${ENV_NAME} -c conda-forge -c bioconda \
    qiime2=${QIIME2_VERSION} \
    qiime2-dev=${QIIME2_VERSION} \
    q2-types=${QIIME2_VERSION} \
    q2-metadata=${QIIME2_VERSION} \
    q2-feature-classifier=${QIIME2_VERSION} \
    q2-diversity=${QIIME2_VERSION} \
    q2-compositional=${QIIME2_VERSION} \
    q2-feature-table=${QIIME2_VERSION} \
    python=3.9

echo ""
echo "================================================"
echo "QIIME 2 ${QIIME2_VERSION} installation complete!"
echo "================================================"
echo ""
echo "To activate the environment, run:"
echo "  conda activate ${ENV_NAME}"
echo ""
echo "To verify installation, run:"
echo "  qiime --version"
echo ""
echo "Note: This environment requires the following packages installed via pip (optional but recommended):"
echo "  - scikit-learn"
echo "  - pandas"
echo "  - numpy"
echo "  - scipy"
echo "  - statsmodels"
echo "  - biopython"
echo "  - networkx"
echo ""
echo "You can install these inside the activated environment using:"
echo "  pip install -r requirements.txt"
echo ""
