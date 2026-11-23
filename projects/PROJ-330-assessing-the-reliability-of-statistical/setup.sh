#!/bin/bash
# Setup script for PROJ-330
# Initializes Python 3.11 virtual environment and installs dependencies
# Checks for R 4.3+ installation

set -e

echo "=== PROJ-330 Setup Script ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Check if Python 3.11+ is available
if [[ ! "$PYTHON_VERSION" =~ ^3\.(1[1-9]|[2-9]|[9][0-9]) ]]; then
    echo "ERROR: Python 3.11 or higher is required."
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

# Check R version
if command -v R &> /dev/null; then
    R_VERSION=$(R --version | head -n 1 | awk '{print $3}')
    echo "Detected R version: $R_VERSION"
    
    # Check if R 4.3+
    if [[ ! "$R_VERSION" =~ ^4\.[3-9] ]]; then
        echo "WARNING: R 4.3 or higher recommended. Current: $R_VERSION"
    fi
else
    echo "WARNING: R not found. Please install R 4.3+ for DE analysis tasks."
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python 3.11 virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# Install R packages if R is available
if command -v R &> /dev/null; then
    echo "Checking R packages..."
    Rscript -e '
    if (!requireNamespace("BiocManager", quietly = TRUE)) {
        install.packages("BiocManager")
    }
    packages <- c("DESeq2", "edgeR", "ggplot2", "dplyr", "tidyr")
    missing <- packages[!sapply(packages, requireNamespace, quietly = TRUE)]
    if (length(missing) > 0) {
        cat("Installing missing R packages:", paste(missing, collapse = ", "), "\n")
        BiocManager::install(missing)
    } else {
        cat("All required R packages are already installed.\n")
    }
    '
fi

echo "=== Setup Complete ==="
echo "To activate the environment, run: source .venv/bin/activate"
echo "To run tests, run: pytest code/tests"