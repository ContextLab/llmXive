# Predicting the Diffusion of Carbon in BCC Metals

This project implements an automated science pipeline to predict carbon diffusion coefficients in Body-Centered Cubic (BCC) metals using compositional data and machine learning.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Access to the internet (for downloading datasets and dependencies)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

The pipeline consists of four main stages executed sequentially:

1. **Download Raw Data**: Fetches the verified HuggingFace dataset.
 ```bash
 python code/01_download.py
 ```

2. **Preprocess Data**: Filters for BCC Carbon entries, computes descriptors, and prepares the dataset.
 ```bash
 python code/02_preprocess.py
 ```

3. **Train Models**: Trains Random Forest, XGBoost, and Elastic Net models, performs permutation tests.
 ```bash
 python code/03_train.py
 ```

4. **Evaluate**: Computes SHAP values, feature importance, and variance partitioning.
 ```bash
 python code/04_evaluate.py
 ```

5. **Validate**: Runs contract tests and verifies output schemas.
 ```bash
 python code/05_validate.py
 ```

## Reproducibility

- **Random Seed**: All stochastic processes are seeded via `code/config.yaml`.
- **Data Integrity**: Raw data checksums are verified during download (`data/raw/`).
- **Determinism**: The pipeline uses deterministic algorithms where possible and fixed seeds for random splits.
- **Logging**: Detailed logs are generated in `logs/` for debugging and audit trails.

## Output Artifacts

- `data/processed/dataset_cleaned.csv`: Processed dataset ready for modeling.
- `data/outputs/model_results.json`: Performance metrics (R², RMSE, MAE, p-value).
- `data/outputs/best_model.pkl`: The trained best-performing model.
- `data/outputs/feature_importance.json`: Ranked features by SHAP magnitude.
- `data/outputs/variance_partition.csv`: Variance decomposition analysis.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

Specific test modules:
- `tests/test_preprocess.py`: Data cleaning and schema validation.
- `tests/test_train.py`: Model training logic and split strategies.
- `tests/test_permutation.py`: Statistical validity of permutation tests.
- `tests/test_contracts.py`: Schema contract validation.
