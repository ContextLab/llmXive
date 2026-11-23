#!/bin/bash
# Setup script for R environment configuration
# This script initializes R environment variables and creates necessary directories

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
R_CONFIG_FILE="${PROJECT_ROOT}/code/config/r_config.yaml"
R_SCRIPT_DIR="${PROJECT_ROOT}/code/scripts"
R_LIBS_DIR="${PROJECT_ROOT}/code/R_libs"

echo "Setting up R environment for llmXive pipeline..."

# Create necessary directories
mkdir -p "${R_SCRIPT_DIR}"
mkdir -p "${R_LIBS_DIR}"
mkdir -p "$(dirname "${R_CONFIG_FILE}")"

# Check if R config exists, create default if not
if [ ! -f "${R_CONFIG_FILE}" ]; then
    echo "Creating default R configuration file..."
    python3 -c "
import sys
sys.path.insert(0, '${PROJECT_ROOT}/code')
from src.r_config import create_default_config
create_default_config()
"
fi

# Verify R is installed
if ! command -v Rscript &> /dev/null; then
    echo "ERROR: Rscript not found in PATH. Please install R 4.3 or later."
    exit 1
fi

echo "R version:"
Rscript --version

# Set environment variables for current session
export R_LIBS_USER="${R_LIBS_DIR}"
export R_MAX_VSIZE="4294967296"  # 4GB default

echo "R environment setup complete."
echo "R_LIBS_USER: ${R_LIBS_USER}"
echo "R_MAX_VSIZE: ${R_MAX_VSIZE}"
echo "R config file: ${R_CONFIG_FILE}"
echo "R script directory: ${R_SCRIPT_DIR}"

# Optional: Install required R packages if not present
if [ "$1" == "--install-packages" ]; then
    echo "Installing required R packages..."
    Rscript -e "
    required_packages <- c('DESeq2', 'edgeR', 'limma', 'ggplot2', 'dplyr', 'tidyr')
    install.packages(required_packages, repos='https://cloud.r-project.org/')
    if (!requireNamespace('BiocManager', quietly = TRUE))
        install.packages('BiocManager')
    BiocManager::install(c('DESeq2', 'edgeR', 'limma'), ask=FALSE, update=FALSE)
    "
    echo "R packages installed."
fi

echo "Setup complete."