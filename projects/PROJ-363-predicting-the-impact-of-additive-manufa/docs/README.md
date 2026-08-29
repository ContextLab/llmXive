# Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## Project Overview

This project implements an automated machine learning pipeline to predict the porosity of 316L Stainless Steel parts produced via Laser Powder Bed Fusion (LPBF). The pipeline ingests manufacturing parameters (laser power, scan speed, hatch spacing, layer thickness), engineers features (Volumetric Energy Density), trains regression models, and provides statistical explainability.

## Architecture

The project follows a modular pipeline structure:

- **Data Acquisition**: Downloads verified 316L LPBF datasets from public repositories (Zenodo).
- **Preprocessing**: Cleans data, handles missing values, normalizes features, and calculates derived metrics.
- **Model Training**: Trains Gradient Boosting and MLP regressors with 5-fold cross-validation.
- **Explainability**: Generates SHAP plots, permutation importance, and bootstrap confidence intervals for statistical significance.

## Directory Structure

```
.
├── code/ # Python modules for the pipeline
│ ├── download_data.py # Data fetching logic
│ ├── preprocess.py # Data cleaning and feature engineering
│ ├── train_models.py # Model training and evaluation
│ ├── analyze_explainability.py # SHAP and statistical analysis
│ ├── utils.py # Shared utilities (logging, hashing, state)
│ └──...
├── data/
│ ├── raw/ # Original downloaded datasets
│ └── processed/ # Cleaned and normalized data
├── models/
│ └── artifacts/ # Trained model pickles (.pkl)
├── results/
│ ├── reports/ # JSON metrics and statistical reports
│ └── plots/ # Generated visualizations (SHAP, etc.)
├── tests/
│ ├── unit/ # Unit tests
│ └── contract/ # Data schema validation tests
├── docs/ # Documentation
├── state/ # Artifact versioning state
├── contracts/ # JSON/YAML schemas for data validation
├── requirements.txt # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-363-predicting-the-impact-of-additive-manufa
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Configure environment variables by copying `.env.example` to `.env` and editing values.

## Usage

The pipeline is executed sequentially. Each script can be run independently from the project root.

### 1. Data Acquisition

Downloads the raw 316L dataset and verifies integrity.

```bash
python code/download_data.py
```

**Output**: `data/raw/316L_lpbf_dataset.csv`

### 2. Preprocessing

Cleans data, handles missing values, normalizes features, and calculates Volumetric Energy Density.

```bash
python code/preprocess.py
```

**Output**: `data/processed/cleaned_316L.csv`

### 3. Model Training

Trains Gradient Boosting and MLP models using 5-fold cross-validation.

```bash
python code/train_models.py
```

**Output**:
- `models/artifacts/gb_model.pkl`
- `models/artifacts/mlp_model.pkl`
- `results/reports/model_metrics.json`

### 4. Explainability Analysis

Generates SHAP plots and statistical significance reports.

```bash
python code/analyze_explainability.py
```

**Output**:
- `results/plots/shap_summary.png`
- `results/reports/significance_report.json`

## Testing

Run the full test suite using pytest:

```bash
pytest tests/ -v
```

Specific test categories:
- **Unit Tests**: `tests/unit/`
- **Contract Tests**: `tests/contract/`

## Data Schema

The pipeline validates data against `contracts/dataset.schema.yaml`. Required columns include:
- `laser_power` (float)
- `scan_speed` (float)
- `hatch_spacing` (float)
- `layer_thickness` (float)
- `porosity` (float)

## License

This project is part of the llmXive automated science pipeline.
