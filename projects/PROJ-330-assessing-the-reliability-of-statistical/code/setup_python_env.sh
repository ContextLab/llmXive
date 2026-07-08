#!/bin/bash
# Setup Python 3.11+ virtual environment with required dependencies
# Requires Python 3.11+ to be installed on the system

set -e

echo "=== Setting up Python environment for PROJ-330 ==="

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Verify Python >= 3.11
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    echo "ERROR: Python version 3.11 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "code/venv" ]; then
    echo "Creating Python 3.11 virtual environment in code/venv..."
    python3 -m venv code/venv
else
    echo "Virtual environment already exists."
fi

# Activate and upgrade pip
source code/venv/bin/activate
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found. Skipping dependency installation."
fi

# Verify critical packages
echo "Verifying Python package installation..."
python3 -c "
import sys
required = ['pandas', 'numpy', 'scikit-learn', 'matplotlib', 'seaborn', 'pyyaml', 'requests', 'tqdm', 'statsmodels']
missing = []
for pkg in required:
    try:
  __import__(pkg)
    except ImportError:
  missing.append(pkg)

if missing:
    print(f'ERROR: Missing required packages: {missing}')
    sys.exit(1)
print('All required Python packages are installed.')
"

echo "=== Python environment setup complete ==="
echo "To activate environment in a new shell:"
echo "  source code/venv/bin/activate"
echo ""
echo "To run Python scripts:"
echo "  python code/main.py"