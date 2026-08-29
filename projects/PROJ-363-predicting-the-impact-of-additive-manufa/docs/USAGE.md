# Usage Guide: 316L Porosity Prediction Pipeline

This guide details how to run, debug, and extend the additive manufacturing porosity prediction pipeline.

## Quick Start

### Step 1: Setup Environment

Ensure you have Python 3.9+ installed. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Run the Pipeline

Execute the scripts in the following order:

```bash
# 1. Download Data
python code/download_data.py

# 2. Preprocess Data
python code/preprocess.py

# 3. Train Models
python code/train_models.py

# 4. Analyze Explainability
python code/analyze_explainability.py
```

## Detailed Script Documentation

### `code/download_data.py`

**Purpose**: Fetches the verified 316L LPBF dataset from Zenodo.

**Configuration**:
- The script looks for `ZENODO_ID` in the environment or defaults to the project-specified ID.
- It verifies the material type is "316L" before proceeding.

**Exit Codes**:
- `0`: Success
- `1`: Download failure or material mismatch

**Artifacts**:
- `data/raw/316L_lpbf_dataset.csv`
- Updates `state.yaml` with the file hash.

### `code/preprocess.py`

**Purpose**: Cleans raw data and engineers features.

**Key Features**:
- **Column Mapping**: Maps synonyms (e.g., "P" -> "laser_power").
- **Fallback Logic**: Checks for existing `VolumetricEnergyDensity` columns; if missing, calculates from raw parameters.
- **Degenerate Detection**: Halts if porosity variance is zero.
- **Normalization**: Scales features to [0, 1].

**Error Handling**:
- Raises `DegenerateDatasetError` if data lacks variance.
- Exits if `contracts/dataset.schema.yaml` validation fails.

**Artifacts**:
- `data/processed/cleaned_316L.csv`

### `code/train_models.py`

**Purpose**: Trains and evaluates regression models.

**Models**:
- **Gradient Boosting Regressor**: Default hyperparameters.
- **MLP Regressor**: Single hidden layer, ReLU activation.
- **Dummy Baseline**: Mean strategy for performance comparison.

**Execution**:
- Uses 5-fold cross-validation.
- CPU-only execution (no GPU).
- Fixed random seed for reproducibility.

**Artifacts**:
- `models/artifacts/gb_model.pkl`
- `models/artifacts/mlp_model.pkl`
- `results/reports/model_metrics.json` (contains RMSE, R², and baseline comparison).

### `code/analyze_explainability.py`

**Purpose**: Interprets model predictions using SHAP and statistical tests.

**Methods**:
- **SHAP**: Generates summary plots.
- **Permutation Importance**: 1,000 permutations.
- **Bootstrap CI**: 1,000 iterations for 95% confidence intervals.
- **Significance Testing**: Calculates p-values to identify significant parameters.

**Constraints**:
- Avoids multicollinearity by not using raw parameters and Volumetric Energy Density simultaneously.

**Artifacts**:
- `results/plots/shap_summary.png`
- `results/reports/significance_report.json`

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
ZENODO_ID=your_zenodo_dataset_id
RANDOM_SEED=42
LOG_LEVEL=INFO
```

### State Management

The `state.yaml` file tracks artifact versions and hashes. Do not edit manually; it is updated automatically by the scripts.

## Troubleshooting

### "Degenerate Dataset" Error

**Cause**: The input data has zero variance in the target variable (porosity).
**Fix**: Verify the raw data source contains a mix of porosity values.

### "Schema Validation Failed"

**Cause**: The data columns do not match `contracts/dataset.schema.yaml`.
**Fix**: Check column names in the raw CSV or update the schema if the data source format has changed.

### Memory Errors during Training

**Cause**: Dataset too large for RAM.
**Fix**: The pipeline is designed for streaming or chunked processing. Ensure the dataset is not excessively large, or reduce the sample size in `preprocess.py` if necessary (though the default is to use the full dataset).

## Extending the Pipeline

### Adding New Models

1. Implement the training logic in `code/train_models.py`.
2. Update `code/train_models.py` to include the new model in the `main` execution flow.
3. Ensure the model is saved to `models/artifacts/`.

### Custom Feature Engineering

Modify `code/preprocess.py` to add new columns or transformation logic. Ensure the new columns are added to the schema in `contracts/dataset.schema.yaml`.

## Support

For issues or questions, refer to the project's `README.md` or the `specs/` directory for detailed design documents.
