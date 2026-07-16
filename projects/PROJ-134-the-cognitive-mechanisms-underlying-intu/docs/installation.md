# Installation Guide

This guide provides step-by-step instructions for setting up the development environment for the Cognitive Mechanisms pipeline.

## Prerequisites

- **Python**: Version 3.11 or higher is required.
- **pip**: The Python package installer.
- **Git**: For version control (optional but recommended).
- **OS**: Linux or macOS is recommended. Windows users may encounter path-related issues.

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd PROJ-134-the-cognitive-mechanisms-underlying-intu
```

## Step 2: Create a Virtual Environment

It is highly recommended to use a virtual environment to isolate dependencies.

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

## Step 3: Install Dependencies

Install all required packages listed in `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencies Include**:
- `pymc>=5.0.0`
- `pandas`
- `numpy`
- `scikit-learn`
- `pyyaml`
- `requests`
- `seaborn`
- `statsmodels`
- `pydantic`
- `pytest`

## Step 4: Verify Installation

Run a quick check to ensure all major libraries are importable:

```bash
python -c "import pymc; import pandas; import numpy; import statsmodels; print('All dependencies installed successfully.')"
```

## Step 5: Initialize Project Structure

Create the necessary directory structure for data and logs:

```bash
python code/setup_directories.py
python code/setup_subdirectories.py
```

This will create:
- `data/raw/`
- `data/processed/`
- `data/logs/`
- `state/`
- `reports/`

## Step 6: Run Tests (Optional)

Verify the installation by running the test suite:

```bash
pytest code/tests/ -v
```

## Troubleshooting Installation

- **Permission Denied**: If you encounter permission errors during installation, ensure your virtual environment is active.
- **Missing Headers**: If compilation fails for `pymc` or `numpy`, ensure you have a C/C++ compiler installed (e.g., `build-essential` on Ubuntu, Xcode Command Line Tools on macOS).
- **Python Version**: Verify your Python version with `python --version`. It must be 3.11+.

## Next Steps

After successful installation, proceed to the [Usage Guide](usage_guide.md) to run the pipeline.