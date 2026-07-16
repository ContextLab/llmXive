# Installation and Environment Setup

This guide explains how to set up the development environment for the grain boundary diffusivity project.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (venv, conda, or virtualenv)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd grain-boundary-diffusivity
```

## Step 2: Create a Virtual Environment

### Using venv (recommended)

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Using conda

```bash
conda create -n grain_boundary python=3.9
conda activate grain_boundary
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` file includes:
- pandas
- numpy
- scikit-learn
- xgboost
- shap
- matplotlib
- requests
- pymatgen
- python-dotenv
- ruff
- black

## Step 4: Configure Environment Variables

Create a `.env` file in the project root with your API keys:

```bash
# Materials Project API Key
MP_API_KEY=your_materials_project_api_key

# OpenKIM API Key (if required)
OPENKIM_API_KEY=your_openkim_api_key

# Optional: Custom paths
DATA_DIR=data
MODEL_DIR=models
```

**Note:** The `.env` file is included in `.gitignore` and should never be committed to version control.

## Step 5: Verify Installation

Run the quickstart validation script to verify all components are correctly installed:

```bash
python code/validate_quickstart.py
```

This script checks:
- Directory structure
- Required files
- Installed dependencies
- Pipeline scripts
- Output artifacts (after running the pipeline)

## Step 6: Run Linting and Formatting (Optional)

The project uses ruff for linting and black for formatting.

```bash
# Check code style
python code/setup_linting_run.py

# Alternatively, run directly
ruff check.
black --check.
```

To fix formatting issues:

```bash
black.
ruff check --fix.
```

## Troubleshooting

### pymatgen Installation Issues

If you encounter issues installing pymatgen, try:

```bash
pip install --upgrade pip
pip install pymatgen --no-cache-dir
```

### API Key Errors

Ensure your `.env` file is correctly formatted and contains valid API keys:

```bash
python code/setup_env.py
```

This script validates that all required API keys are present.

### Memory Issues

The pipeline is designed to run within 7 GB RAM. If you encounter memory issues:
- Ensure no other heavy applications are running
- Consider increasing swap space
- Use a machine with more RAM for large datasets

## Next Steps

After successful installation:
1. Review the `README.md` for an overview of the project
2. Check the `API Reference` for detailed module documentation
3. Run the full pipeline using the steps in `README.md`
4. Explore the `docs/` directory for additional documentation
