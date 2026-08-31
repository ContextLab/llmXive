# Usage Guide: 316L Porosity Prediction Pipeline

This guide provides detailed instructions for running the pipeline components, understanding outputs, and troubleshooting.

## Quick Start

To run the entire pipeline end-to-end:

```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Run the full pipeline
python code/download_data.py && \
python code/preprocess.py && \
python code/train_models.py && \
python code/analyze_explainability.py
```

## Step-by-Step Execution

### Step 1: Download Data (`code/download_data.py`)

**Purpose**: Fetches the raw 316L Stainless Steel LPBF dataset from a verified public repository.

**Arguments**: None (configurable via environment variables if needed).

**Behavior**:
1. Fetches the dataset.
2. Verifies the material type is "316L Stainless Steel". If not, raises a `Material Mismatch` error.
3. Computes SHA-256 checksum and updates `state.yaml`.

**Expected Output**:
- `data/raw/` directory containing the raw CSV file.
- Updated `state.yaml` with the file hash.

### Step 2: Preprocess Data (`code/preprocess.py`)

**Purpose**: Cleans data, validates against schema, imputes missing values, and engineers features.

**Behavior**:
1. Loads `contracts/dataset.schema.yaml` and validates raw data.
2. Maps column synonyms (e.g., "P" -> "laser_power").
3. Imputes missing numerical values using the **median**.
4. Calculates Volumetric Energy Density ($E_v = P / (v \cdot h \cdot t)$).
5. Checks for degenerate datasets (zero porosity variance).
6. Normalizes features to [0, 1].
7. Splits data into `X_raw` (raw parameters) and `X_derived` (Ev only).

**Expected Output**:
- `data/processed/cleaned_316L.csv`
- `data/processed/X_raw.csv`
- `data/processed/X_derived.csv`

### Step 3: Train Models (`code/train_models.py`)

**Purpose**: Trains and evaluates Gradient Boosting and MLP models.

**Behavior**:
1. Loads `cleaned_316L.csv` and splits into `X_raw` and `X_derived`.
2. Performs 5-fold Cross-Validation for:
 - Gradient Boosting Regressor
 - MLP Regressor
 - Dummy Baseline (for comparison)
3. Computes RMSE and R² for each fold.

**Expected Output**:
- `models/artifacts/` (`.pkl` files for best models).
- `results/reports/model_metrics_raw.json`
- `results/reports/model_metrics_derived.json`

### Step 4: Analyze Explainability (`code/analyze_explainability.py`)

**Purpose**: Interprets model behavior using SHAP and statistical tests.

**Behavior**:
1. Loads the best performing models.
2. Calculates SHAP values and generates summary plots.
3. Performs Permutation Importance (1,000 permutations).
4. Calculates Bootstrap Confidence Intervals (1,000 iterations).
5. Computes p-values to determine statistical significance (p < 0.05).

**Expected Output**:
- `results/plots/shap_summary_raw.png`
- `results/plots/shap_summary_derived.png`
- `results/reports/significance_report_raw.json`
- `results/reports/significance_report_derived.json`
- `results/reports/feature_comparison.json`

## Troubleshooting

### "Material Mismatch" Error
- **Cause**: The downloaded dataset does not contain "316L Stainless Steel".
- **Fix**: Verify the source URL in `code/download_data.py` or check the dataset metadata.

### "Degenerate Dataset" Error
- **Cause**: The target variable (porosity) has zero variance in the loaded data.
- **Fix**: Check the data source for filtering issues or empty datasets.

### Missing Dependencies
- **Cause**: Required Python packages are not installed.
- **Fix**: Run `pip install -r requirements.txt`.

## Output Interpretation

- **RMSE/R²**: Lower RMSE and higher R² indicate better model performance.
- **SHAP Summary Plot**: Shows the impact of each feature on the model output. Red points indicate high feature values, blue indicates low values.
- **P-values**: Features with p < 0.05 are considered statistically significant drivers of porosity.

## Advanced Configuration

To change the random seed, modify the `SEED` constant in `code/utils.py` or set the `PYTHONHASHSEED` environment variable.
