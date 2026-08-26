# Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## Project Overview

This project implements a machine learning pipeline to predict the porosity of 316L Stainless Steel parts produced via Laser Powder Bed Fusion (LPBF). The pipeline ingests public manufacturing parameter data, preprocesses it, trains regression models, and provides statistical explainability to identify critical process parameters.

## Project Structure

```
.
├── code/ # Python implementation scripts
│ ├── __init__.py
│ ├── utils.py # Shared utilities (logging, hashing, state)
│ ├── download_data.py # Data acquisition from Zenodo
│ ├── preprocess.py # Data cleaning, normalization, feature engineering
│ ├── train_models.py # Model training (GBR, MLP, Baseline)
│ ├── analyze_explainability.py # SHAP, Permutation Importance, Bootstrap CI
│ ├── save_processed_data.py
│ ├── save_significance_report.py
│ ├── update_state_artifacts.py
│ └── linting_config.py
├── data/
│ ├── raw/ # Downloaded raw datasets
│ └── processed/ # Cleaned and normalized datasets
├── models/
│ └── artifacts/ # Trained model pickles (.pkl)
├── results/
│ ├── reports/ # JSON metrics and significance reports
│ └── plots/ # SHAP and visualization outputs
├── contracts/ # Data schema definitions
│ └── dataset.schema.yaml
├── state/
│ └── state.yaml # Artifact versioning and hashes
├── tests/ # Unit and contract tests
│ ├── unit/
│ └── contract/
├── docs/ # Documentation
│ └── README.md
├── requirements.txt # Python dependencies
└──.env.example # Environment configuration template
```

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

The pipeline is executed in sequential stages. Each stage produces artifacts required by the next.

### 1. Data Acquisition

Downloads the verified 316L LPBF dataset from Zenodo, verifies material type, and computes checksums.

```bash
python code/download_data.py
```

**Output**: `data/raw/316L_lpbf_dataset.csv` (or similar), updated `state.yaml`.

### 2. Preprocessing

Cleans data, handles missing values, normalizes features, and engineers Volumetric Energy Density.

```bash
python code/preprocess.py
```

**Output**: `data/processed/cleaned_316L.csv`, updated `state.yaml`.

### 3. Model Training

Trains Gradient Boosting and MLP regressors with 5-fold cross-validation and a dummy baseline.

```bash
python code/train_models.py
```

**Output**: `models/artifacts/`, `results/reports/model_metrics.json`, updated `state.yaml`.

### 4. Explainability & Statistical Analysis

Generates SHAP plots, Permutation Importance, and Bootstrap Confidence Intervals.

```bash
python code/analyze_explainability.py
```

**Output**: `results/plots/shap_summary.png`, `results/reports/significance_report.json`, updated `state.yaml`.

### 5. State Management

Updates the `state.yaml` file with hashes of all generated artifacts (can be run manually after each stage or automatically by the stage scripts).

```bash
python code/update_state_artifacts.py
```

## Configuration

Create a `.env` file in the project root based on `.env.example` for environment-specific settings (e.g., API keys if needed, though this project primarily uses public data).

## Testing

Run unit and contract tests using `pytest`:

```bash
pytest tests/ -v
```

## Contributing

1. Ensure code passes linting (`ruff`/`flake8`) and formatting (`black`).
2. Add tests for new functionality.
3. Update documentation as needed.

## License

[Insert License Information]
