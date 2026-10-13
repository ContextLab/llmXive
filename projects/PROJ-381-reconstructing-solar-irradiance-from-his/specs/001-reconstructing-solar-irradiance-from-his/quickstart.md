# Quickstart: Reconstructing Solar Irradiance from Historical Sunspot Records

## Prerequisites
- Python 3.11+
- `git`
- ~Adequate free disk space (on the order of gigabytes).
- Internet access (dataset download)

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

`.env.example` (managed via `python-dotenv`, loaded in `code/config.py`):

```dotenv
# Root directory for raw/processed/artifacts data
DATA_ROOT=data

# Pinned random seed for all stochastic steps
RANDOM_SEED=42

# Bootstrap iterations (spec requires a sufficiently large number of iterations, e.g., on the order of thousands)
BOOTSTRAP_ITER=1000
```

## Data Preparation

```bash
# Download verified datasets (GSN, SILSO, CMIP6), record checksums, validate it against the schema
python -m code.data.ingestion

# Gap filling, cycle detection, feature engineering; writes preprocessed_data.parquet
python -m code.data.preprocessing
```

## Running the Full Analysis

```bash
# Orchestrate everything end‑to‑end (will automatically skip steps that lack required data)
python -m code.main
```

Or **if a verified TSI dataset becomes available**, run the pipeline step‑by‑step:

```bash
python -m code.models.train        # conditional: skipped with a logged note if TSI unavailable
python -m code.analysis.sensitivity   # conditional: skipped if no model was trained
python -m code.models.predict      # conditional: skipped if no model was trained
python -m code.analysis.comparison # runs with available data; reports omitted metrics as null
```

**Current data status**: No verified open SORCE/TIM TSI or baseline source from the early mission period exists., so training is skipped, the Cycle‑Agnostic fallback is **not instantiated**, and reconstruction is omitted. The final report flags `tsi_available = false` and `baseline_available = false`; all metrics that depend on these data are reported as `null` with explanatory notes.

## Testing

```bash
pytest tests/ -v
```

The suite verifies:
- download + checksum verification;
- gap‑filling logic (interpolation vs. proxy thresholds);
- cycle‑boundary alignment within ±6 months of SILSO maxima;
- categorical Cycle‑ID one‑hot encoding;
- conditional model training (or graceful skip);
- `preprocessed_data.parquet` and `tsi_reconstruction_1610_2002.parquet` (when produced) conform to `contracts/*.schema.yaml`;
- bootstrap uses a sufficiently large number of iterations.; and
- the conditional logic correctly handles the absence of TSI data.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Download failure on ingestion | Verified URL temporarily unreachable | Re‑run; CI aborts with a clear error if persistent. |
| Training skipped | No verified TSI dataset (expected today) | Documented limitation; provide a verified TSI source to enable. |
| Missing `preprocessed_data.parquet` | Preprocessing crashed before write | Check logs; the script must always write the parquet on success — rerun `python -m code.data.preprocessing`. |
| No variance results | `BOOTSTRAP_ITER` < 1000 | Set it to 1000 in `.env` (spec‑mandated). |
| Baseline metrics absent | 2007 baseline unavailable | Expected; the `baseline_available` flag is false in the report. |
| Reconstruction omitted | No trained model (TSI missing) | Expected; the pipeline proceeds with remaining analyses. |
