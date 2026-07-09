#!/bin/bash
#
# Environment Setup Script
# Initializes Python 3.11 virtual environment and R renv environment
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
R_ENV_DIR="${PROJECT_ROOT}/renv"

echo "=== Setting up Python environment ==="

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Warning: Python 3.11 not found. Using available python3"
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3.11"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR"
    $PYTHON_CMD -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
    pip install -r "${PROJECT_ROOT}/requirements.txt"
else
    echo "Warning: requirements.txt not found"
fi

echo "=== Setting up R environment ==="

# Check R installation
if ! command -v R &> /dev/null; then
    echo "Error: R is not installed. Please install R 4.3 or later."
    exit 1
fi

R_VERSION=$(R --version | head -n1 | awk '{print $3}')
echo "Found R version: $R_VERSION"

# Create renv environment if it doesn't exist
if [ ! -d "$R_ENV_DIR" ]; then
    echo "Initializing renv environment at $R_ENV_DIR"
    cd "$PROJECT_ROOT"
    Rscript -e "renv::init()"
else
    echo "R environment already exists at $R_ENV_DIR"
fi

# Install required R packages
echo "Installing R packages (DESeq2, edgeR, etc.)..."
Rscript -e "renv::install(c('DESeq2', 'edgeR', 'data.table', 'jsonlite', 'argparse'))"

echo "=== Environment setup complete ==="
echo "Python virtual environment: $VENV_DIR"
echo "R renv environment: $R_ENV_DIR"
echo ""
echo "To activate Python environment: source $VENV_DIR/bin/activate"
echo "To activate R environment: Rscript -e 'renv::load()'"
