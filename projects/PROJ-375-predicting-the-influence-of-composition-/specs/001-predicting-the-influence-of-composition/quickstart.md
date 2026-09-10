# Quickstart: Predicting CTE of Metallic Glasses from Composition

## Prerequisites
1. **Python 3.11** installed (or use the provided `requirements.txt`).  
2. A free **Materials Project API key** – obtain it at <https://materialsproject.org/dashboard> and export it:  

```bash
export MP_API_KEY="YOUR_API_KEY_HERE"
```

3. GitHub Actions runner (optional) – the steps below run locally on any Linux/macOS/Windows machine.

## Installation
```bash
git clone https://github.com/your-org/metallic-glass-cte.git
cd metallic-glass-cte
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ruff check .   # lint check (optional)
```

## Step‑by‑Step Run‑Book

| Step | Command | Description |
|------|---------|-------------|
| 0 | `python -m pip install -r requirements.txt` | Install pinned dependencies. |
| 1 | `python -m code.ingestion.fetch_materials_project` | Pull **raw** MP data (including the Thermal Properties endpoint) and **AFLOWlib** data, save to `data/raw/`, compute checksum. |
| 2 | `python -m code.features.descriptors` | Generate the four compositional descriptors, compute VIF, apply fallback (PCA + Ridge) if needed, and write `data/processed/clean_mg_data.parquet`. |
| 3 | `python -m code.modeling.train` | Perform stratified split (by alloy family), CV, hyper‑parameter search, and save final models to `models/`. |
| 4 | `python -m code.modeling.baseline` | Train a baseline linear regression model that uses the **weighted‑average elemental CTE** as its sole predictor, evaluate on the test set, and write `results/baseline_metrics.json`. |
| 5 | `python -m code.modeling.evaluate` | Evaluate on test set, compute R², MAE, RMSE, and write `results/model_performance.json`. |
| 6 | `python -m code.modeling.permutation_test` | Run 1 000 permutation iterations, output p‑value and null distribution (`results/permutation_null_distribution.npy`). |
| 7 | `python -m code.modeling.feature_importance` | Produce `results/feature_importance.csv` and `results/spearman_correlation.txt`. |
| 8 | `python -m code.utils.log_resources` | Append runtime and memory usage to `results/runtime_log.txt` and generate `results/computational_efficiency.json`. |

## Verifying the Output
```bash
# Check that the cleaned dataset has the required columns
python - <<'PY'
import pandas as pd, pyarrow.parquet as pq
df = pd.read_parquet('data/processed/clean_mg_data.parquet')
print(df.columns.tolist())
print(df.head())
PY

# Validate the schema
python - <<'PY'
import json, yaml, jsonschema, pandas as pd
with open('contracts/mg_dataset.schema.yaml') as f:
    schema = yaml.safe_load(f)
df = pd.read_parquet('data/processed/clean_mg_data.parquet')
jsonschema.validate(instance=df.to_dict(orient='records')[0], schema=schema)
print("Schema validation passed.")
PY
```

## Expected Runtime & Memory (GitHub Actions free tier)
- Total wall‑clock time: **≈ 2 h** (including API download).  
- Peak RAM: **≈ 4 GB** (well under the 7 GB limit).  

If any step exceeds 30 min (training) or the overall job exceeds 6 h, the pipeline aborts and reports the violation (Constitution Principle VII). The final `results/computational_efficiency.json` will contain a pass/fail flag indicating whether the limits were respected.

## Directory Structure (created by the CI pipeline)
```
code/
├── ingestion/
├── features/
├── modeling/
├── utils/
├── .ruff.toml
├── __init__.py
data/
├── raw/
├── processed/
├── checksums.txt
models/
├── linear_regression.pkl
├── random_forest.pkl
└── baseline_linear.pkl
results/
├── baseline_metrics.json
├── model_performance.json
├── feature_importance.csv
├── spearman_correlation.txt
├── runtime_log.txt
└── computational_efficiency.json
docs/
├── quickstart.md
└── research.md
```
