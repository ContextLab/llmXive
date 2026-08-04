# Quickstart: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Prerequisites

- Python 3.11+
- Sufficient free disk space (for raw and processed data)
- Substantial RAM (streaming reduces peak usage)
- Internet access (for downloading datasets)
- Materials Project API Key (set as `MP_API_KEY` environment variable)

## Installation

```bash
# Clone repository and navigate to project
cd projects/PROJ-170-predicting-catalytic-activity-from-elect

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt** (pinned versions):
```txt
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
xgboost==2.0.2
shap==0.44.0
datasets==2.14.6
matplotlib==3.8.2
seaborn==0.13.0
pytest==7.4.3
pymatgen==2023.10.1
mp-api==0.35.0
```

## Data Download

Run the download script to fetch and stream datasets:

```bash
python code/download_data.py
```

This script:
1. Streams OC20 Experimental dataset from Hugging Face.
2. Fetches MP descriptors via API (cached locally).
3. Saves raw samples to `data/raw/`.
4. Computes and records checksums.

**Output**: `data/raw/oc20_sample.parquet`, `data/raw/mp_cache.json`

## Descriptor Extraction

Run the extraction script to derive electronic descriptors from raw structures:

```bash
python code/extract_descriptors.py
```

This script:
1. Parses OC20 atomic structures.
2. Computes d-band center, p-band center, Bader charges, and coordination numbers.
3. Saves derived descriptors to `data/processed/descriptors.parquet`.

**Output**: `data/processed/descriptors.parquet`

## Preprocessing

Run the preprocessing pipeline to align, impute, and scale data:

```bash
python code/preprocess.py
```

This script:
1. Aligns datasets on `composition`, `surface_facet`, `synthesis_condition` (fuzzy match).
2. Imputes missing descriptors with k=5 nearest neighbors (geometry-aware).
3. Scales numeric features to zero mean, unit variance.
4. Logs excluded entries.

**Output**: `data/processed/aligned_dataset.csv`, `outputs/alignment_log.json`, `outputs/imputation_log.json`

## Model Training

Train XGBoost and Volcano baseline models:

```bash
python code/train.py
```

This script:
1. Performs 5-fold CV grid search for XGBoost (max_depth ∈ {5,7}, learning_rate ∈ {low, high}, n_estimators will be evaluated across a range of values to determine optimal model performance.).
2. Trains Volcano baseline (quadratic fit) on d-band center and activation barrier.
3. Performs statistical test (t-test or Wilcoxon) on absolute errors.
4. Saves best model and metrics.

**Output**: `code/models/xgboost_best.pkl`, `outputs/model_metrics.json`

## Reduced Model Evaluation (SC-003)

Train the top-5 reduced model:

```bash
python code/evaluate_reduced.py
```

This script:
1. Identifies top descriptors from SHAP analysis.
2. Trains XGBoost on only these descriptors.
3. Calculates R² ratio against full model.

**Output**: `outputs/reduced_model_metrics.json`

## Interpretability Analysis

Compute SHAP values and generate feature importance plot:

```bash
python code/interpret.py
```

This script:
1. Computes SHAP values for the final XGBoost model.
2. Ranks descriptors by mean absolute SHAP impact.
3. Generates bar plot of top descriptors.

**Output**: `outputs/feature_importance.png`, `outputs/shap_ranking.json`

## Generate Final Report

Compile all results into a single report:

```bash
python code/report.py
```

This script:
1. Aggregates model metrics, statistical test results, and SHAP rankings.
2. Compares top 5 descriptors to Nørskov et al. reference.
3. Includes data lineage (checksums, HF commit hashes).

**Output**: `outputs/final_report.md`

## Verification

Run tests to ensure pipeline integrity:

```bash
pytest tests/ -v
```

Tests cover:
- Contract validation (schema compliance)
- End-to-end pipeline execution
- Unit tests for preprocessing and imputation

## Expected Runtime

- **Download**: ~10-30 min (depends on network)
- **Descriptor Extraction**: ~30-60 min (depends on sample size)
- **Preprocessing**: ~5-15 min
- **Training**: ~30-60 min (XGBoost grid search)
- **Interpretability**: ~5-10 min
- **Total**: ≤3 hours on CPU (well within 6h limit)

