# Usage Guide

This document provides detailed instructions for using each script in the pipeline.

## 1. Data Acquisition

### `code/download_data.py`

Fetches the verified 316L LPBF dataset from the canonical source (Zenodo/OpenML).

**Execution:**
```bash
python code/download_data.py
```

**Process:**
1. Reads the verified URL from `research.md` (via `state.yaml` verification record).
2. Downloads the full dataset to `data/raw/`.
3. Computes a cryptographic checksum and updates `state.yaml`.

**Error Handling:**
- If the network request fails, times out, or returns a 404, the script raises a `RuntimeError` and exits.
- **No synthetic data** is generated. The pipeline halts to ensure data authenticity.

## 2. Data Preprocessing

### `code/preprocess.py`

Cleans, normalizes, and engineers features for modeling.

**Execution:**
```bash
python code/preprocess.py
```

**Process:**
1. Loads raw data from `data/raw/`.
2. **Column Mapping**: Maps synonyms (e.g., 'P' -> 'laser_power', 'v' -> 'scan_speed') to standard schema.
3. **Imputation**: Fills missing numerical values with the **median** of the column.
4. **Energy Density**: Calculates Volumetric Energy Density ($E_v = P / (v \cdot h \cdot t)$).
 - Filters out rows where parameters are <= 0.
 - Falls back to existing `energy_density` column if raw parameters are missing.
5. **Normalization**: Scales input features to [0, 1].
6. **Feature Subsets**: Creates `X_raw.csv` (raw parameters) and `X_derived.csv` (Ev only).
7. **Degenerate Check**: If porosity variance is zero, writes `data/processed/degenerate_flag.json` and exits cleanly (code 0).
8. **Validation**: Validates processed data against `contracts/dataset.schema.yaml`.
9. **Output**: Saves `data/processed/cleaned_316L.csv` and updates `state.yaml`.

## 3. Model Training

### `code/train_models.py`

Trains Gradient Boosting and MLP regressors using 5-fold Cross-Validation.

**Execution:**
```bash
python code/train_models.py
```

**Process:**
1. Loads `data/processed/cleaned_316L.csv`, `X_raw.csv`, and `X_derived.csv`.
2. **Training**:
 - Trains Gradient Boosting and MLP on `X_raw`.
 - Trains Gradient Boosting and MLP on `X_derived`.
3. **Baseline**: Trains a `DummyRegressor` (mean strategy) for both subsets.
4. **Metrics**: Computes RMSE and R² for each fold and the mean.
5. **Success Criterion SC-001**:
 - Fails if `Best Model R²` <= `Dummy R²` AND `Best Model R²` < 0.65.
6. **Model Selection**: Compares mean R² scores of the best models from both subsets and selects the winner. Writes selection to `state/selected_model.yaml`.
7. **Output**:
 - Saves models to `models/artifacts/`.
 - Saves metrics to `results/reports/model_metrics_raw.json` and `model_metrics_derived.json`.
 - Updates `state.yaml`.

## 4. Explainability & Analysis

### `code/analyze_explainability.py`

Generates SHAP plots and performs statistical significance testing.

**Execution:**
```bash
python code/analyze_explainability.py
```

**Process:**
1. Loads the best model selected in `state/selected_model.yaml`.
2. **SHAP Analysis**:
 - Calculates SHAP values.
 - Generates a summary plot saved to `results/plots/shap_summary_{subset}.png`.
 - Performs **SHAP Bootstrap** (1000 resamples) to calculate 95% Confidence Intervals for each feature.
3. **Permutation Importance**:
 - Performs 1,000 permutations.
 - Calculates p-values and determines significance (p < 0.05).
4. **Model Comparison**:
 - Compares feature importance ranks between `X_raw` and `X_derived` models using Spearman correlation.
 - Generates a side-by-side bar chart.
5. **Output**:
 - Saves unified statistical report: `results/reports/unified_statistical_analysis_{subset}.json`.
 - Saves feature comparison: `results/reports/feature_comparison.json`.
 - Updates `state.yaml`.

## 5. Pipeline Orchestration

### `code/run_pipeline_with_timer.py`

Executes the full pipeline with timing enforcement.

**Execution:**
```bash
python code/run_pipeline_with_timer.py
```

**Process:**
1. Records start timestamp to `results/reports/pipeline_start.json`.
2. Executes scripts in order:
 - `download_data.py`
 - `preprocess.py`
 - `train_models.py`
 - `analyze_explainability.py`
3. Records end timestamp to `results/reports/pipeline_end.json`.
4. Calculates total duration.
5. **Constraint**: If duration > 6 hours, exits with code 1.

## 6. Validation & Verification

### `tests/contract/test_success_criteria.py`

Verifies all project success criteria.

**Execution:**
```bash
python tests/contract/test_success_criteria.py
```

**Checks:**
- SC-001: Model R² performance.
- SC-002: Statistical significance of features.
- SC-003: Pipeline duration.
- SC-004: Data completeness.

### `code/verify_artifacts.py`

Validates artifact integrity against `state.yaml`.

**Execution:**
```bash
python code/verify_artifacts.py
```

**Checks:**
- Computes SHA-256 hashes of all files in `data/`, `models/`, and `results/`.
- Compares against hashes in `state.yaml`.
- Reports any mismatches.