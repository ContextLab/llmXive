# Quickstart: Predicting CTE of Metallic Glasses from Composition

## Prerequisites
1. **Python 3.11** (or use the provided `requirements.txt`).  
2. A free **Materials Project API key** – obtain it at <https://materialsproject.org/dashboard> and export it:  

```bash
export MP_API_KEY="YOUR_API_KEY_HERE"
```

3. GitHub Actions runner (optional) – the steps below run locally on any OS.

## Installation
```bash
git clone 
cd metallic-glass-cte
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ruff check .   # optional lint
```

## Step‑by‑Step Run‑Book

| Step | Command | Description |
|------|---------|-------------|
| 0 | `pip install -r requirements.txt` | Install pinned dependencies. |
| 1 | `python -m code.ingestion.fetch_data` | Load the curated CSV, augment with MP/AFLOW entries, filter for metallic‑glass, compute coverage & power analysis, write `data/processed/clean_alloy_data.parquet`. |
| 2 | `python -m code.features.compute_descriptors` | Generate the four compositional descriptors, compute VIF, apply PCA‑Ridge fallback if needed, write the cleaned parquet file. |
| 3 | `python -m code.modeling.split_data` | Perform GroupKFold stratified split (fallback to random 80/20); outputs `train.parquet` and `test.parquet`. |
| 4 | `python -m code.modeling.train` | Run 5‑fold CV, grid‑search for Linear Regression & Random Forest, fit final models, save `models/*.pkl`. |
| 5 | `python -m code.modeling.baseline` | Train the baseline weighted‑average elemental CTE model; save metrics to `results/baseline_metrics.json`. |
| 6 | `python -m code.modeling.evaluate` | Evaluate test‑set performance for all models; write `results/model_performance.json`. |
| 7 | `python -m code.modeling.permutation_test` | Execute ≥ 1 000‑iteration permutation test; output `results/permutation_null_distribution.npy` and p‑value. |
| 8 | `python -m code.modeling.feature_importance` | Produce `results/feature_importance.csv` and `results/correlation_diagnostics.json`. |
| 9 | `python -m code.utils.log_resources` | Log runtime & peak memory; generate `results/computational_efficiency.json`. |
| 10 | `python -m code.tests.validate_contracts` | Run unit tests that validate example rows against the JSON‑Schema contracts. |

## Verifying the Output
```bash
# 1️⃣ Check that the processed dataset contains all required columns
python - <<'PY'
import pandas as pd
df = pd.read_parquet('data/processed/clean_alloy_data.parquet')
print(df.columns.tolist())
print(df.head())
PY

# 2️⃣ Validate the dataset against the schema
python - <<'PY'
import yaml, jsonschema, pandas as pd
with open('contracts/mg_dataset.schema.yaml') as f:
    schema = yaml.safe_load(f)
df = pd.read_parquet('data/processed/clean_alloy_data.parquet')
example = df.iloc[0].to_dict()
jsonschema.validate(instance=example, schema=schema)
print("Schema validation passed.")
PY
```

## Expected Runtime & Memory (GitHub Actions free tier)
- **Total wall‑clock time**: ≈ 2 h (including API download).  
- **Peak RAM**: ≈ 3 GB (well under the 7 GB limit).  

If any step exceeds the allocated resources, the pipeline aborts and `results/computational_efficiency.json` will contain `"limits_passed": false`.

## Early‑Termination Notice
If Phase 0 determines that **≥ 95 %** of metallic‑glass entries cannot be retrieved **or** that fewer than **500** usable samples are available, the pipeline will **stop after ingestion** and output `results/ingestion_coverage.json` together with a clear “Specification Amendment Required” flag. No modeling or downstream analysis will be performed in that case.

## Seed Fixing for Reproducibility
All scripts set `np.random.seed(42)` and `random.seed(42)` at import time, ensuring deterministic behavior across runs (Constitution Principle I).

---
