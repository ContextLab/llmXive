# Quickstart: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Overview

This guide shows how to run a **minimal end‑to‑end** version of the research pipeline on a small
subset (the first 100 rows) of the curated metallic‑glass CSV. The command produces
`results/sample_output.parquet`, which contains all columns required by the
`mg_dataset.schema.yaml` contract and passes JSON‑Schema validation.

## Prerequisites

1. **Python 3.11** (or use the provided `requirements.txt`).
2. A free **Materials Project API key** (required only for the full pipeline; the quick‑start
 does **not** contact external APIs). Export it in your shell:

```bash
export MP_API_KEY="YOUR_API_KEY"
```

## Installation

```bash
git clone <repository‑url>
cd <repo‑root>
python -m venv.venv
source.venv/bin/activate # Windows:.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the minimal pipeline

```bash
python -m pipeline.run --sample 100
```

The script will:

1. Load `data/raw/curated_metallic_glass.csv`.
2. Keep only the first *N* rows (`N` defaults to 100, can be changed with `--sample`).
3. Compute the four compositional descriptors
 - `weighted_mean_atomic_radius`
 - `electronegativity_variance`
 - `vec` (valence‑electron concentration)
 - `atomic_size_coefficient_of_variation`
4. Add a per‑row SHA‑256 `checksum` for provenance.
5. Write the enriched table to `results/sample_output.parquet`.
6. Validate the table against the JSON‑Schema contract; the script exits with status 0
 only if validation succeeds.

## Verify the output

```bash
# Inspect the parquet file
python - <<'PY'
import pandas as pd
df = pd.read_parquet('results/sample_output.parquet')
print(df.head())
print("Columns:", df.columns.tolist())
PY

# Schema validation (requires PyYAML and jsonschema, already in the environment)
python - <<'PY'
import yaml, jsonschema, pandas as pd
with open('contracts/mg_dataset.schema.yaml') as f:
 schema = yaml.safe_load(f)
df = pd.read_parquet('results/sample_output.parquet')
jsonschema.validate(instance=df.iloc[0].to_dict(), schema=schema)
print("Schema validation passed.")
PY
```

## Expected runtime & resources

- **Wall‑clock time**: < 30 seconds (100 rows).
- **Peak RAM**: < 200 MB.
- **CPU cores**: 1 (the script does not spawn parallel workers).

The quick‑start command is deliberately lightweight and safe to run on any platform,
making it ideal for CI checks, teaching, or rapid prototyping.
