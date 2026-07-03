# Quantifying the Impact of Grain Boundary Character on Diffusivity

This project implements an automated science pipeline to quantify the relationship between grain boundary character (misorientation, Σ value, boundary plane) and atomic diffusivity in polycrystalline materials. It utilizes atomistic simulation data from Materials Project, OpenKIM, and NIST, processes it using `pymatgen`, and trains a gradient-boosted tree model (XGBoost) to predict diffusivity.

## Project Structure

```
.
├── code/ # Python implementation modules
│ ├── utils.py # Logging, checksums, random seeds
│ ├── error_handling.py # Data insufficiency error classes
│ ├── geometry_parser.py # Structure parsing and feature extraction
│ ├── preprocess.py # Data cleaning and validation
│ ├── diagnostics.py # Collinearity and MI analysis
│ ├── train.py # Model training and hyperparameter tuning
│ ├── validate.py # Cross-validation and bias testing
│ └── interpret.py # SHAP analysis and sensitivity sweeps
├── data/
│ ├── raw/ # Downloaded POSCAR/CIF files
│ ├── processed/ # Parquet datasets
│ └── metadata.yaml # Data provenance
├── models/ # Trained model artifacts
├── artifacts/
│ ├── figures/ # SHAP plots, diagnostic charts
│ └── reports/ # JSON reports (metrics, validation)
├── specs/ # Design documents
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Installation and Environment Setup

### Prerequisites

- **Python**: Version 3.9 or higher is required.
- **Package Manager**: `pip` (included with Python) or `conda`.
- **API Keys**: Access to the following external services is required:
 - [Materials Project](https://materialsproject.org): Requires an API key.
 - [OpenKIM](https://openkim.org): Requires an API key for specific force fields (if applicable).

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd PROJ-117-quantifying-the-impact-of-grain-boundary
```

### Step 2: Create a Virtual Environment

It is highly recommended to isolate dependencies using a virtual environment.

**Using `venv` (Standard Python):**
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

**Using `conda`:**
```bash
conda create -n grain_boundary python=3.9
conda activate grain_boundary
```

### Step 3: Install Dependencies

Install the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Note on `pymatgen`**: This package may require additional system libraries (e.g., `libxml2`, `gsl`). If you encounter compilation errors, consider using `conda` to install `pymatgen` instead:
```bash
conda install -c conda-forge pymatgen
```

### Step 4: Configure Environment Variables

The pipeline requires API keys to fetch data from external sources. Create a `.env` file in the project root to store these secrets. **Do not commit this file to version control.**

```bash
touch.env
```

Add the following lines to `.env`, replacing the placeholders with your actual keys:

```ini
MP_API_KEY=your_materials_project_api_key_here
OPENKIM_API_KEY=your_openkim_api_key_here
```

**Security Warning**: Ensure your `.env` file is listed in `.gitignore`. The project should be configured to ignore this file.

### Step 5: Verify Installation

Run a quick check to ensure all dependencies are importable:

```bash
python -c "import pandas; import pymatgen; import xgboost; import shap; print('All dependencies installed successfully.')"
```

## Quick Start

Once the environment is set up, you can run the full pipeline:

1. **Download Data**:
 ```bash
 python code/download.py
 ```
2. **Parse Geometry**:
 ```bash
 python code/geometry_parser.py
 ```
3. **Preprocess**:
 ```bash
 python code/preprocess.py
 ```
4. **Run Diagnostics**:
 ```bash
 python code/diagnostics.py
 ```
5. **Train Model**:
 ```bash
 python code/train.py
 ```
6. **Validate**:
 ```bash
 python code/validate.py
 ```
7. **Interpret**:
 ```bash
 python code/interpret.py
 ```

Refer to `quickstart.md` for detailed execution parameters and output locations.

## License

This project is part of the llmXive automated science pipeline. See the LICENSE file for details.
