# Quickstart Guide: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

This guide provides instructions for setting up the environment, configuring API keys, and running the full pipeline to generate thermal expansion predictions for metallic glasses.

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- API Keys for external data sources (see below)

## 1. Installation

Clone the repository and install dependencies:

```bash
cd PROJ-375-predicting-the-influence-of-composition-
pip install -r code/requirements.txt
```

**Note:** The `requirements.txt` includes `ruff` for linting, `mendeleev` for elemental properties, and `scikit-learn` for modeling.

## 2. Environment Configuration

The pipeline requires API keys for data sources. Set these as environment variables before running the scripts.

### Required API Keys

- **Materials Project**: `MP_API_KEY`
 - Get your key at: https://next-gen.materialsproject.org/api
- **AFLOWlib**: `AFLOWlib_API_KEY` (Optional, used as primary source)
 - Get your key at:
- **Zenodo Fallback**: `ZENODO_ID` (Optional, defaults to '1234567' if not set)

### Setting Environment Variables

**Linux/macOS:**
```bash
export MP_API_KEY="your_materials_project_key"
export AFLOWlib_API_KEY="your_aflow_key"
export ZENODO_ID="your_zenodo_dataset_id"
```

**Windows (PowerShell):**
```powershell
$env:MP_API_KEY="your_materials_project_key"
$env:AFLOWlib_API_KEY="your_aflow_key"
$env:ZENODO_ID="your_zenodo_dataset_id"
```

## 3. Running the Pipeline

The pipeline is executed via the main training script which orchestrates data ingestion, feature extraction, model training, and evaluation.

```bash
python code/main.py
```

If `code/main.py` is not present as a single entry point, run the stages sequentially:

### Stage 1: Data Ingestion
```bash
python code/ingestion/fetch_data.py
```
*Output:* `data/raw/mp_afraw.csv`

### Stage 2: Feature Extraction & Cleaning
```bash
python code/ingestion/save_clean_data.py
```
*Output:* `data/processed/clean_mg_data.parquet`

### Stage 3: Model Training & Evaluation
```bash
python code/modeling/train.py
```
*Output:* `code/models/`, `results/metrics.json`, `results/feature_importance.csv`

## 4. Expected Outputs

Upon successful completion, the following artifacts will be generated:

- **Raw Data:** `data/raw/mp_afraw.csv` (Composition, CTE, Amorphous Flag)
- **Processed Data:** `data/processed/clean_mg_data.parquet` (With calculated descriptors)
- **Models:** `code/models/` (Serialized `.pkl` files and metadata)
- **Metrics:** `results/metrics.json` (R², MAE, RMSE, Permutation P-value, Divergence Analysis)
- **Feature Importance:** `results/feature_importance.csv`
- **Correlations:** `results/correlations.csv`
- **Divergence Analysis:** `results/divergence.csv`

### Example Output Snippet (`results/metrics.json`)

```json
{
 "baseline_type": "null_model",
 "spec_root_cause_SC001": "elemental_cte_data_unavailable",
 "r2_score": 0.65,
 "mae": 1.2e-5,
 "rmse": 1.5e-5,
 "permutation_p_value": 0.001,
 "sc003_divergence_metric": 0.85,
 "sc003_interpretation": "non_linear_effects_detected",
 "spec_root_cause_SC003": "linear_match_unsound_for_nonlinear_models",
 "vif_warning": "High VIF detected for size_mismatch (VIF=6.2) - retained per FR-002",
 "runtime_seconds": 120.5,
 "peak_memory_mb": 2500
}
```

## 5. Validation

To validate the pipeline setup without running the full training (e.g., if data is already present):

```bash
python code/main.py --validate
```

This checks for the existence of required directories, valid API keys, and schema compliance of existing data files.

## 6. Troubleshooting

- **DataFetchError:** If the script raises `DataFetchError: No valid metallic glass entries found`, ensure your API keys are correct and the `ZENODO_ID` is valid if using the fallback.
- **Resource Limit Exceeded:** If `ResourceLimitExceeded` is raised, check that your system has sufficient RAM (limit: 7GB) and that `n_jobs` in `code/modeling/train.py` is set to 2 or fewer.
- **Missing `mendeleev` Data:** If `mendeleev` fails to find an element, verify the composition strings in the raw data are valid chemical formulas (e.g., "Zr50Cu40Al10").

## 7. Documentation

For detailed research methodology and data source citations, refer to `docs/research.md`.
