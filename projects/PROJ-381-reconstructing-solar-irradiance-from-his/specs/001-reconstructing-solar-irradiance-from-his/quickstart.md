# Quickstart: Reconstructing Solar Irradiance from Historical Sunspot Records

## Prerequisites
- Python 3.11 or newer
- `git` (to clone the repository)
- ~Several GB of free disk space
- Internet access (for dataset download)

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/solar-irradiance-reconstruction.git
cd solar-irradiance-reconstruction

# 2. Create a clean virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Environment Configuration
A minimal `.env.example` is provided. Copy it to `.env` if you need to override defaults (e.g., custom data directory).

```bash
cp .env.example .env
```

**`.env.example` contents**

```dotenv
# Directory where raw and processed data will be stored
DATA_ROOT=data

# Random seed for reproducibility
RANDOM_SEED=42

# Number of bootstrap iterations (default 1000)
BOOTSTRAP_ITER=1000
```

The pipeline reads these variables via `python-dotenv` (already a dependency).

## Data Preparation

```bash
# Download and verify raw datasets (GSN, SILSO, CMIP6, optional TSI)
python code/data/ingestion.py
# → creates data/raw/*.parquet and records checksums

# Preprocess (gap filling, cycle detection, feature engineering with categorical Cycle ID)
python code/data/preprocessing.py
# → output: data/processed/preprocessed_data.parquet and data/processed/solar_cycles.parquet
```

## Running the Full Analysis

```bash
# 1. Train models and perform leave‑one‑cycle‑out CV (if a verified TSI dataset is available)
python code/models/train.py
# If TSI is missing, the script will emit a warning and skip training, proceeding to step 3.

# 2. Sensitivity analysis for inconsistency tolerance
python code/analysis/sensitivity.py

# 3. Generate the historical reconstruction (1610‑2002)
python code/models/predict.py

# 4. Compare against CMIP6 proxy and (if available) the 2007 baseline
python code/analysis/comparison.py
```

All outputs are written under `data/artifacts/` and `data/processed/`.  
If the SORCE/TIM TSI dataset cannot be downloaded (currently unavailable), the training step will be skipped, and the fallback model will be used for reconstruction; the comparison step will still run using CMIP6 as an independent proxy.

## Testing

```bash
pytest tests/ -v
```

The test suite checks:
- Successful download and checksum verification of raw files.
- Correct execution of preprocessing (including gap‑filling logic and categorical Cycle ID creation).
- Model training produces non‑empty pickle files **when** TSI data is present and writes a validation report; otherwise it reports the limitation without error.
- Reconstruction file contains the expected columns and no missing dates.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `DataValidationError` on ingestion | One of the verified URLs is temporarily unavailable | Re‑run after a few minutes; the CI runner will abort with a clear error if the problem persists. |
| `MemoryError` during preprocessing | Attempting to load the full raw dataset into memory on a very low‑memory runner | Reduce the chunk size in `preprocessing.py` (the script already streams the raw parquet files). |
| Missing model artifacts after training | No verified satellite TSI data available; training was skipped as documented | Provide a verified TSI source or accept that model training cannot be performed under current data constraints. |
| No variance‑analysis results | Bootstrap iteration count set to 0 | Check `BOOTSTRAP_ITER` in `.env`; must be ≥ 1000. |
| Unexpected warnings about CMIP6 usage | CMIP6 is now used **only** for comparison, not training | No action needed; the pipeline follows the updated methodology. |

---  