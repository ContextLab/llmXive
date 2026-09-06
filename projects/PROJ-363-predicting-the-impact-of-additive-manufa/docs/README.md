# Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

## Project Overview

This project implements an automated science pipeline to predict the porosity of 316L Stainless Steel produced via Laser Powder Bed Fusion (LPBF) based on manufacturing parameters. The pipeline downloads real-world experimental data, preprocesses it, trains machine learning models, and performs statistical explainability analysis.

## Prerequisites

- Python 3.9+
- Virtual environment tool (`venv`)
- Git

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-363-predicting-the-impact-of-additive-manufa
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Project Structure

```
.
├── code/ # Implementation scripts
│ ├── download_data.py # Fetches real 316L LPBF dataset
│ ├── preprocess.py # Cleans, normalizes, and engineers features
│ ├── train_models.py # Trains GB and MLP models with CV
│ ├── analyze_explainability.py # SHAP and Permutation Importance analysis
│ ├── run_pipeline_with_timer.py # Orchestrates full pipeline with timing
│ └── utils.py # Shared utilities (logging, hashing, state)
├── data/
│ ├── raw/ # Raw downloaded dataset
│ └── processed/ # Cleaned and normalized data
├── models/
│ └── artifacts/ # Trained model pickles (.pkl)
├── results/
│ ├── plots/ # SHAP summary plots and comparison charts
│ └── reports/ # JSON metrics and statistical analysis reports
├── state/
│ └── state.yaml # Artifact versioning and hashes
├── tests/ # Unit and contract tests
├── contracts/ # Data schemas
└── docs/ # Documentation
```

## Quickstart

Run the entire pipeline end-to-end with a timer wrapper:

```bash
python code/run_pipeline_with_timer.py
```

This script executes the following steps in sequence:
1. **Download Data**: Fetches the verified 316L LPBF dataset from the canonical source.
2. **Preprocess**: Cleans data, imputes missing values, normalizes features, and calculates Volumetric Energy Density.
3. **Train Models**: Trains Gradient Boosting and MLP regressors on both raw and derived feature subsets using 5-fold CV.
4. **Analyze**: Performs SHAP analysis, permutation importance, and statistical significance testing.

The pipeline enforces a 6-hour time limit. If exceeded, it exits with code 1.

## Command-Line Arguments

### `code/download_data.py`
- No arguments required. Fetches the dataset defined in `research.md` and `state.yaml`.
- **Behavior**: Fails loudly if the real source is unreachable. No synthetic fallback.

### `code/preprocess.py`
- No arguments required. Loads `data/raw/`, applies schema validation, and outputs to `data/processed/`.
- **Behavior**: Handles degenerate datasets by writing a flag file and exiting cleanly.

### `code/train_models.py`
- No arguments required. Trains models on `data/processed/` subsets.
- **Behavior**: Validates Success Criterion SC-001 (Model R² > Dummy R² or R² ≥ 0.65).

### `code/analyze_explainability.py`
- No arguments required. Loads the best selected model and generates SHAP/Permutation reports.
- **Behavior**: Generates unified statistical reports with 95% Bootstrap CIs.

### `code/run_pipeline_with_timer.py`
- No arguments required. Orchestrates the full pipeline.
- **Output**: Writes start/end timestamps to `results/reports/` and validates duration.

## Verification & Success Criteria

The pipeline validates the following success criteria:
- **SC-001**: Model performance exceeds dummy baseline or meets R² ≥ 0.65.
- **SC-002**: At least one feature has statistical significance (p < 0.05) in Permutation Importance.
- **SC-003**: Pipeline completes within 6 hours.
- **SC-004**: Final dataset has zero missing values.

Run the validation suite:
```bash
python tests/contract/test_success_criteria.py
```

## Data Integrity

All artifacts (data, models, reports) are versioned in `state.yaml` with SHA-256 hashes.
Verify integrity:
```bash
python code/verify_artifacts.py
```

## License

This project is part of the llmXive automated science pipeline.
