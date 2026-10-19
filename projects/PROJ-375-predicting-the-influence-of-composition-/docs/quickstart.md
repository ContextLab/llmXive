# Quickstart Guide: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

## Overview

This guide walks you through setting up the environment, configuring the required API keys, and running the complete research pipeline end‑to‑end. The pipeline consists of three core scripts:

1. **Data ingestion** – fetches raw metallic‑glass data from the Materials Project and AFLOWlib.
2. **Model training** – prepares features, splits the data, and trains Linear Regression and Random Forest models.
3. **Model evaluation** – evaluates the trained models, runs permutation significance testing, and produces diagnostic artefacts.

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

- `code/ingestion/fetch_data.py` – contacts MP (via `pymatgen.ext.matproj.MPRester`) and AFLOWlib (via the public REST API at ` Name or service not known)"))]). It saves raw JSON responses under `data/raw/` and records SHA‑256 checksums in `data/checksums.txt`.
- `code/modeling/train.py` – loads the cleaned dataset, computes descriptors, performs VIF filtering, splits the data, and trains Linear Regression and Random Forest models. Model artefacts are written to `models/`.
- `code/modeling/evaluate.py` – evaluates the test split, writes `results/model_performance.json`, runs the ≥ 1000‑iteration permutation test, and produces divergence diagnostics.

## (c) Verified data sources

The pipeline relies on two external, publicly accessible data sources:

1. **Materials Project (MP)**
 - Accessed through `pymatgen.ext.matproj.MPRester`.
 - Query endpoint: *Thermal Properties* (`/materials/v2/` with `include=properties` and `amorphous=true`).
 - Provides composition, thermal‑expansion coefficient (`thermal_expansion_coefficient`), and metadata such as `material_type`.

2. **AFLOWlib**
 - Accessed via its public REST API: `.
 - Query parameters: `structure_type=amorphous` and `properties=composition,cte`.
 - Returns JSON records with composition strings and CTE values.

Both sources are queried **without any synthetic fallback**. If a request fails (e.g., network error, missing API key), the loader raises an exception and the pipeline aborts, ensuring full provenance.

## Logging and provenance

All scripts initialise logging with `setup_logging()` from `code/utils/io.py`. The logger writes to `logs/pipeline.log`, which records:

- The exact URLs requested for MP and AFLOWlib.
- Query parameters used.
- HTTP response status codes.
- SHA‑256 checksums of the raw JSON payloads.

This log file serves as the immutable provenance record for the entire run.

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
```

The `code/setup_directories.py` script (included in the repository) can be run beforehand to materialise all required folders:

```bash
python code/setup_directories.py
```

After running the pipeline, you should see artefacts such as:

- `data/raw/<source>_raw.json`
- `data/processed/clean_mg_data.parquet`
- `models/linear_regression.pkl`, `models/random_forest.pkl`
- `results/model_performance.json`
- `logs/pipeline.log`

These files can be inspected to verify that the pipeline executed successfully and that all provenance information is captured.