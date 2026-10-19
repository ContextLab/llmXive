# Quickstart: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Overview

This guide walks you through setting up the environment, configuring the required API keys, and running the complete research pipeline end‑to‑end. The pipeline consists of three core scripts that fetch data, train models, and evaluate performance.

The exact command sequence is:

```bash
python code/ingestion/fetch_data.py && \
python code/modeling/train.py && \
python code/modeling/evaluate.py
```

## (a) Setting up the `MP_API_KEY` environment variable

The Materials Project (MP) API key is required to query the MP REST endpoint for thermal‑expansion data.

1. Obtain a free API key from the Materials Project dashboard: <https://next-gen.materialsproject.org/api>.
2. Export the key in your shell before running the pipeline.

```bash
# Linux / macOS
export MP_API_KEY="YOUR_MP_API_KEY"

# Windows PowerShell
$env:MP_API_KEY="YOUR_MP_API_KEY"
```

*Note:* The AFLOWlib API does not require an API key for the public REST endpoint used in this project, but the script will still look for `AFLOWLIB_API_KEY` if you have one. Setting it is optional.

```bash
export AFLOWLIB_API_KEY="YOUR_AFLOWLIB_KEY" # optional
```

## (b) Exact run commands

The pipeline is orchestrated with three independent Python scripts. Run them sequentially **in a single command line** as shown below. Each script will log its activity to `logs/pipeline.log`.

```bash
python code/ingestion/fetch_data.py && \
python code/modeling/train.py && \
python code/modeling/evaluate.py
```

### Step 1: Data Ingestion

```bash
python code/ingestion/fetch_data.py
```

- Contacts Materials Project via `pymatgen.ext.matproj.MPRester` for entries containing `thermal_expansion_coefficient`.
- Queries AFLOWlib public REST API at ` for supplemental metallic‑glass data.
- Saves raw JSON responses under `data/raw/mp_data.json` and `data/raw/aflow_data.json`.
- Records SHA‑256 checksums in `data/checksums.txt`.
- Applies amorphous detection (primary: `material_type` field or "glass" in description; documented fallbacks: tags, structure_type, missing space‑group).
- Extracts compositional descriptors using `pymatgen.core.Composition` and `mendeleev` elemental properties.
- Writes cleaned dataset to `data/processed/clean_mg_data.parquet`.
- Emits `data/results/ingestion_stats.json` and `data/results/data_availability_report.json`.
- **Any failure to fetch real data aborts the pipeline** — no synthetic fallback is performed.

### Step 2: Model Training

```bash
python code/modeling/train.py
```

- Loads the cleaned dataset from `data/processed/clean_mg_data.parquet`.
- Computes Variance Inflation Factors (VIF) over the four descriptors.
- Drops descriptors with VIF > 5.0, prioritising retention of `weighted_mean_atomic_radius`.
- **Fallback**: if all descriptors exceed VIF > 5.0, applies PCA retaining exactly the first two principal components.
- Performs a stratified train‑test split by alloy family (or random 80/20 if stratification fails).
- Trains Linear Regression and Random Forest models with 5‑fold cross‑validation.
- Grid search over Random Forest hyperparameters: `n_estimators=[100,200,500]`, `max_depth=[None,10,20]`, `min_samples_leaf=[1,2]`.
- Writes train and test splits to `data/processed/train.parquet` and `data/processed/test.parquet`.
- Serialises final models to `models/linear_regression.pkl` and `models/random_forest.pkl`.
- Writes training metrics to `results/training_metrics.json`.

### Step 3: Model Evaluation

```bash
python code/modeling/evaluate.py
```

- Loads the test split from `data/processed/test.parquet`.
- Loads serialized models from `models/`.
- Computes R², MAE, RMSE on the held‑out test set for both models.
- Runs a ≥1000‑iteration permutation test to assess statistical significance.
- Flags a "Null Result" when R² < 0.3.
- Writes `results/model_performance.json` conforming to `contracts/model_metrics.schema.yaml`.

## (c) Verified data sources

The pipeline relies on two external, publicly accessible data sources:

### Materials Project (MP)

- **Access method**: `pymatgen.ext.matproj.MPRester` (requires `MP_API_KEY` environment variable)
- **Query endpoint**: Materials Project API v2 Thermal Properties endpoint
- **Query criteria**: `{"thermal_expansion_coefficient": {"$exists": True}}`
- **Properties retrieved**: `material_id`, `pretty_formula`, `thermal_expansion_coefficient`, `material_type`, `structure`, `tags`, `spacegroup`, `description`, `thermo`, `elasticity`
- **Amorphous filtering**: Primary check on `material_type` field for "amorphous" or "glass"; secondary check for "glass" keyword in `description` field
- **Data guarantee**: Publicly accessible; requires free API key registration at <https://next-gen.materialsproject.org/api>

### AFLOWlib

- **Access method**: Public REST API (no authentication required)
- **API endpoint**: `
- **Query parameters**: `property=thermal_expansion_coefficient`, `keywords=glass`, `format=json`
- **Response format**: JSON array of material records with composition and CTE values
- **Availability**: Public, no API key required
- **Graceful degradation**: If AFLOWlib request fails (network error, timeout, or returns no results), the pipeline logs a warning and continues with Materials Project data only (still satisfies FR‑001)

Both sources are queried **without any synthetic fallback**. If a request fails permanently and no data can be retrieved, the loader raises an exception and the pipeline aborts, ensuring full provenance.

## Logging and provenance

All scripts initialise logging to `logs/pipeline.log`, which records:

- Exact timestamps of API requests
- Query parameters used for each endpoint
- HTTP response status codes and counts
- SHA‑256 checksums of raw JSON payloads
- Amorphous filtering statistics (entries filtered, reason for filtering)
- Descriptor extraction statistics (entries with valid descriptors, entries dropped)
- Training statistics (split sizes, cross‑validation scores, model hyperparameters)
- Evaluation metrics (R², MAE, RMSE, permutation p‑values)

This log file serves as the immutable provenance record for the entire run and can be inspected to verify data sources, query parameters, and processing decisions.

## Directory structure (created on demand)

The following project folders are created automatically by the toolkit's `paths` helper when first referenced:

```
code/
 ingestion/
 features/
 modeling/
 utils/
data/
 raw/
 processed/
 results/
models/
figures/
docs/
logs/
tests/
 unit/
 integration/
```

After running the pipeline, you should see artefacts such as:

- `data/raw/mp_data.json` — raw Materials Project API response
- `data/raw/aflow_data.json` — raw AFLOWlib API response
- `data/checksums.txt` — SHA‑256 checksums of raw JSON files
- `data/processed/clean_mg_data.parquet` — cleaned dataset with descriptors and checksums
- `data/processed/train.parquet` — training split
- `data/processed/test.parquet` — test split
- `data/results/ingestion_stats.json` — ingestion completeness ratio
- `data/results/data_availability_report.json` — per‑source statistics
- `models/linear_regression.pkl` — serialized Linear Regression model
- `models/random_forest.pkl` — serialized Random Forest model
- `results/training_metrics.json` — training cross‑validation scores
- `results/model_performance.json` — test set evaluation metrics and permutation p‑values
- `logs/pipeline.log` — full execution log with provenance

These files can be inspected to verify that the pipeline executed successfully and that all provenance information is captured.

## Installation and environment setup

```bash
# Create a virtual environment
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Export your Materials Project API key
export MP_API_KEY="your_key_here"

# Run the pipeline
python code/ingestion/fetch_data.py && \
python code/modeling/train.py && \
python code/modeling/evaluate.py

# Check the logs
tail -f logs/pipeline.log
```

## Expected runtime and resource usage

- **Total wall‑clock time**: ~1–2 hours (including API download and model training)
- **Peak RAM**: ~4 GB (well under the 7 GB limit)
- **CPU cores used**: 2 (enforced by `n_jobs=2` in scikit‑learn)
- **GPU required**: No

If any step exceeds the resource limits (≤2 CPU cores, ≤7 GB RAM, ≤6 hours), the pipeline logs a violation and reports it in `results/computational_efficiency.json`.

## Troubleshooting

### "Environment variable MP_API_KEY is required"

You must export your Materials Project API key before running the pipeline:

```bash
export MP_API_KEY="your_api_key"
python code/ingestion/fetch_data.py
```

### "No metallic‑glass entries with CTE were found after filtering"

This indicates that the Materials Project API returned no entries matching the amorphous detection criteria. Possible causes:
- API endpoint or query structure has changed (check Materials Project documentation)
- Network connectivity issue (check your internet connection)
- API rate limiting (wait a few minutes and retry)

### "Test split not found at data/processed/test.parquet"

Ensure that `python code/modeling/train.py` completed successfully before running `python code/modeling/evaluate.py`.

## Verifying the output

After the pipeline completes, verify that the cleaned dataset has the required columns:

```bash
python - <<'PY'
import pandas as pd
df = pd.read_parquet('data/processed/clean_mg_data.parquet')
required_cols = [
 'material_id', 'composition', 'cte',
 'weighted_mean_atomic_radius', 'electronegativity_variance', 'vec',
 'atomic_size_coefficient_of_variation',
 'source_method', 'amorphous_flag', 'checksum'
]
missing = [c for c in required_cols if c not in df.columns]
if missing:
 print(f"ERROR: Missing columns: {missing}")
else:
 print(f"✓ All required columns present")
 print(f"✓ Dataset shape: {df.shape}")
 print(f"✓ No missing values in descriptors: {df[['weighted_mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_size_coefficient_of_variation']].notna().all().all()}")
PY
```

Validate the schema:

```bash
python - <<'PY'
import yaml
import jsonschema
import pandas as pd

with open('specs/001-predicting-the-influence-of-composition/contracts/mg_dataset.schema.yaml') as f:
 schema = yaml.safe_load(f)

df = pd.read_parquet('data/processed/clean_mg_data.parquet')
for idx, row in df.iterrows():
 try:
 jsonschema.validate(instance=row.to_dict(), schema=schema)
 except jsonschema.ValidationError as e:
 print(f"Row {idx} failed validation: {e.message}")
 break
else:
 print(f"✓ Schema validation passed for all {len(df)} rows")
PY
```

Check that evaluation metrics were generated:

```bash
python - <<'PY'
import json
from pathlib import Path

metrics_path = Path('results/model_performance.json')
if metrics_path.exists():
 with open(metrics_path) as f:
 metrics = json.load(f)
 print(f"✓ Model performance metrics:")
 print(f" - Linear Regression R²: {metrics['linear_regression'].get('r2', 'N/A')}")
 print(f" - Random Forest R²: {metrics['random_forest'].get('r2', 'N/A')}")
 print(f" - Permutation test p-value: {metrics['permutation_test'].get('p_value', 'N/A')}")
 print(f" - Null result flag: {metrics.get('null_result_flag', 'N/A')}")
else:
 print("ERROR: Model performance metrics not found")
PY
```

## Next steps

After the pipeline completes successfully:

1. **Inspect the logs**: `cat logs/pipeline.log` to verify data sources and processing decisions
2. **Review ingestion statistics**: `cat data/results/ingestion_stats.json` to see the number of entries collected
3. **Check model performance**: `cat results/model_performance.json` to see R², MAE, RMSE, and p‑values
4. **Proceed to downstream tasks**: T002 (amorphous filtering refinement), T003 (VIF/PCA handling), T004 (baseline comparison), etc.

For detailed research methods, data sources, and results interpretation, see `docs/research.md` (to be generated after initial run).