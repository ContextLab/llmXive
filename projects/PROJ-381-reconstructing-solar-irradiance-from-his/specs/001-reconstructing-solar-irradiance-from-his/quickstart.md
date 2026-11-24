# Quickstart: Reconstructing Solar Irradiance from Historical Sunspot Records

## Prerequisites
- Python 3.11+  
- `git`  
- ~Adequate free disk space (datasets + intermediate files)  
- Internet access (to download the open datasets)

## Installation

```bash
git clone https://github.com/your-org/solar-irradiance-reconstruction.git
cd solar-irradiance-reconstruction
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Configuration

```bash
cp .env.example .env
```

`.env.example` (loaded by `code/config.py` via `python-dotenv`):

```dotenv
# Root directory for raw/processed/artifacts data
DATA_ROOT=data

# Pinned random seed for all stochastic steps
RANDOM_SEED=42

# Number of bootstrap iterations (spec requires ≥ 1000)
BOOTSTRAP_ITER=1000
```

## Data Preparation

```bash
# Download verified datasets (SILSO cycles + CMIP6 solar forcing)
python -m code.data.ingestion

# Preprocess SILSO data, detect cycles, engineer features; writes preprocessed_data.parquet
python -m code.data.preprocessing
```

## Running the Full Analysis

```bash
# Orchestrates the entire pipeline; steps that lack required data are skipped automatically
python -m code.main
```

### Step‑by‑step (if a verified TSI dataset becomes available)

```bash
python -m code.models.train        # skipped with a log note if TSI or GSN unavailable
python -m code.analysis.sensitivity   # skipped if no model was trained
python -m code.models.predict      # skipped if no model was trained
python -m code.analysis.comparison # runs with whatever data is present; missing metrics are `null`
```

**Current data status**: No verified open SORCE/TIM TSI or 2007 baseline are available, and a verified GSN dataset is also missing. Consequently, model training, reconstruction, and any metric that depends on predictions will be omitted. The final JSON report contains `gsn_available = false`, `tsi_available = false`, and `baseline_available = false`; all dependent metrics are `null` with explanatory notes.

## Testing
```bash
pytest tests/ -v
```
The test suite verifies:
- Successful download + checksum verification of the two verified datasets (SILSO, CMIP series).  
- Correct gap‑filling logic (interpolation vs. proxy).  
- Cycle‑boundary detection within ±6 months of SILSO maxima.  
- One‑hot encoding of `cycle_id`.  
- Conditional model training (or graceful skip) based on data availability.  
- Conformance of `preprocessed_data.parquet` and, when produced, `tsi_reconstruction_1610_2002.parquet` to `contracts/dataset.schema.yaml`.  
- Bootstrap uses a sufficiently large number of iterations (seeded).  
- Proper logging of `gsn_available`, `tsi_available`, and `baseline_available` flags.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Download error in ingestion | Verified URL temporarily unreachable | Re‑run; CI will abort with a clear error if persistent. |
| Model training skipped | No verified TSI or GSN dataset (expected) | Provide a verified source to enable training. |
| `preprocessed_data.parquet` missing | Preprocessing crashed before write | Check logs; rerun `python -m code.data.preprocessing`. |
| Bootstrap iterations < 1000 | `BOOTSTRAP_ITER` incorrectly set | Set `BOOTSTRAP_ITER=1000` (or higher) in `.env`. |
| Baseline metrics absent | 2007 baseline unavailable | Expected; `baseline_available = false` in the report. |
| Reconstruction file missing | No trained model (TSI or GSN missing) | Expected; pipeline proceeds with remaining analyses. |

---



