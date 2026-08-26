# Usage Guide

This guide details the execution flow and expected outputs for the Additive Manufacturing Porosity Prediction pipeline.

## Execution Flow

The pipeline is designed to run sequentially. Do not skip stages as later stages depend on artifacts produced by earlier ones.

### Step 1: Download Data

**Script**: `code/download_data.py`

**Purpose**:
- Fetches the 316L Stainless Steel LPBF dataset from Zenodo.
- Verifies the material type is "316L".
- Computes SHA-256 checksums.
- Updates `state.yaml`.

**Command**:
```bash
python code/download_data.py
```

**Expected Output**:
- `data/raw/<dataset_file>.csv`
- `state.yaml` updated with download hash.

**Troubleshooting**:
- If download fails, check internet connectivity and the Zenodo record ID.
- If material verification fails, the script will exit with an error.

### Step 2: Preprocess Data

**Script**: `code/preprocess.py`

**Purpose**:
- Loads raw data.
- Maps column synonyms (e.g., "P" -> "laser_power").
- Handles missing values via median imputation.
- Normalizes features to [0, 1].
- Calculates Volumetric Energy Density (VED) if raw parameters are available.
- Validates against `contracts/dataset.schema.yaml`.
- Detects and halts on degenerate datasets (zero variance in porosity).

**Command**:
```bash
python code/preprocess.py
```

**Expected Output**:
- `data/processed/cleaned_316L.csv`
- `state.yaml` updated with processed data hash.

**Troubleshooting**:
- `DegenerateDatasetError`: The dataset has zero variance in the target variable; no meaningful model can be trained.
- `SchemaValidationFailed`: The data does not match the expected schema; check raw data integrity.

### Step 3: Train Models

**Script**: `code/train_models.py`

**Purpose**:
- Loads `data/processed/cleaned_316L.csv`.
- Splits data into features (X) and target (y).
- Trains Gradient Boosting Regressor (5-fold CV).
- Trains MLP Regressor (5-fold CV).
- Trains a Dummy Baseline (mean strategy) for comparison.
- Computes RMSE and R² for each fold and the mean.
- Saves models and metrics.

**Command**:
```bash
python code/train_models.py
```

**Expected Output**:
- `models/artifacts/gradient_boosting.pkl`
- `models/artifacts/mlp_regressor.pkl`
- `results/reports/model_metrics.json` (contains per-fold and mean metrics, plus baseline comparison).
- `state.yaml` updated with model hashes.

**Troubleshooting**:
- `FileNotFoundError`: Ensure `data/processed/cleaned_316L.csv` exists.
- `MemoryError`: Reduce dataset size or increase system memory (unlikely for typical 316L datasets).

### Step 4: Explainability Analysis

**Script**: `code/analyze_explainability.py`

**Purpose**:
- Loads the best performing model.
- Calculates SHAP values and generates a summary plot.
- Performs Permutation Importance (1,000 permutations).
- Calculates Bootstrap Confidence Intervals (1,000 iterations) for SHAP values.
- Computes p-values and identifies statistically significant parameters (p < 0.05).
- Saves plots and reports.

**Command**:
```bash
python code/analyze_explainability.py
```

**Expected Output**:
- `results/plots/shap_summary.png`
- `results/reports/significance_report.json`
- `state.yaml` updated with report hashes.

**Troubleshooting**:
- `ModelNotFoundError`: Ensure models were trained in Step 3.
- `MulticollinearityWarning`: The script checks for simultaneous use of raw parameters and VED; if detected, it will adjust inputs.

## State Management

The `state.yaml` file tracks the versioning and integrity of all artifacts. It is automatically updated by each stage script. You can manually verify the state by running:

```bash
python code/update_state_artifacts.py
```

## Environment Variables

Copy `.env.example` to `.env` and configure as needed. Currently, the pipeline relies on public data sources and does not require external API keys, but this file is provided for future extensibility.

## Reproducibility

To ensure reproducibility:
1. Use the same Python version.
2. Install exact dependency versions from `requirements.txt`.
3. Ensure the random seed is fixed (handled internally by `utils.py`).
4. Verify `state.yaml` hashes match the expected values for the dataset.
