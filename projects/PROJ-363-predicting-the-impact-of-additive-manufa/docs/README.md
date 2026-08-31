# Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## Project Overview

This project implements an automated machine learning pipeline to predict the porosity of 316L Stainless Steel parts produced via Laser Powder Bed Fusion (LPBF). The pipeline ingests process parameters (laser power, scan speed, hatch spacing, layer thickness), engineers Volumetric Energy Density (Ev), trains regression models, and performs statistical explainability analysis (SHAP, Permutation Importance, Bootstrap CIs).

## Prerequisites

- Python 3.9+
- pip (package installer)
- A Unix-like environment (Linux/macOS) or WSL on Windows

## Installation

1. **Clone the repository** (if applicable) and navigate to the project root.

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Directory Structure

```text
.
├── code/ # Implementation scripts
│ ├── download_data.py # Fetches raw 316L dataset
│ ├── preprocess.py # Cleans, validates, and engineers features
│ ├── train_models.py # Trains GB and MLP models
│ ├── analyze_explainability.py # SHAP and statistical analysis
│ └── utils.py # Shared utilities
├── data/
│ ├── raw/ # Downloaded raw CSVs
│ └── processed/ # Cleaned datasets (cleaned_316L.csv)
├── models/
│ └── artifacts/ # Trained.pkl model files
├── results/
│ ├── reports/ # JSON metrics and significance reports
│ └── plots/ # SHAP summary plots (PNG)
├── contracts/ # Data schema definitions (YAML)
├── state/ # Artifact versioning state (state.yaml)
├── tests/ # Unit and contract tests
└── docs/ # Documentation
```

## Usage Instructions

The pipeline is executed sequentially. Run the following scripts in order:

### 1. Data Acquisition
Downloads the verified 316L LPBF dataset and validates the material type.
```bash
python code/download_data.py
```
*Output*: `data/raw/` (raw CSV), updates `state.yaml`.

### 2. Preprocessing
Validates schema, handles missing values (median imputation), normalizes features, and engineers Volumetric Energy Density.
```bash
python code/preprocess.py
```
*Output*: `data/processed/cleaned_316L.csv`, `data/processed/X_raw.csv`, `data/processed/X_derived.csv`.

### 3. Model Training
Trains Gradient Boosting and MLP regressors using 5-fold Cross-Validation on both `X_raw` and `X_derived` subsets.
```bash
python code/train_models.py
```
*Output*: `models/artifacts/*.pkl`, `results/reports/model_metrics_*.json`.

### 4. Explainability & Statistical Analysis
Generates SHAP plots, calculates Permutation Importance, and computes Bootstrap Confidence Intervals with p-values.
```bash
python code/analyze_explainability.py
```
*Output*: `results/plots/shap_summary_*.png`, `results/reports/significance_report_*.json`, `results/reports/feature_comparison.json`.

### 5. State Verification
Verifies that all artifacts match their recorded hashes in `state.yaml`.
```bash
python code/verify_artifacts.py
```

## Configuration

- **Seed**: Set via `code/utils.py` (default `42`).
- **Data Source**: The pipeline fetches data from a verified public source (Zenodo/OpenML) as defined in `code/download_data.py`. No synthetic data is generated.

## Testing

Run the test suite to verify pipeline integrity:

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v
pytest tests/contract/ -v
```

## License

This project is part of the llmXive automated science pipeline.
