#!/bin/bash
# Alternative installation script using Conda/Mamba for better dependency management
# This script creates a dedicated environment and installs the required tools.

set -e

if ! command -v conda &> /dev/null; then
    echo "Conda is not installed. Please install Miniconda or Anaconda first."
    exit 1
fi

ENV_NAME="plant-defense-env"

echo "Creating conda environment: ${ENV_NAME}"
conda create -n ${ENV_NAME} -y python=3.11

echo "Activating environment and installing dependencies..."
# Install bioconda packages
conda run -n ${ENV_NAME} conda install -y -c bioconda -c conda-forge \
    hisat2 \
    fastp \
    subread \
    samtools \
    bedtools

echo "Installing Python dependencies..."
conda run -n ${ENV_NAME} pip install -r requirements.txt

echo "Verifying installations..."
conda run -n ${ENV_NAME} hisat2 --version
conda run -n ${ENV_NAME} fastp --version
conda run -n ${ENV_NAME} featureCounts --version

echo "Conda environment setup complete. Activate with: conda activate ${ENV_NAME}"
