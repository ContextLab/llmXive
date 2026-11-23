# Quickstart: Calibration of Predictive Intervals for Time‑Series Forecasts

## Prerequisites
- Python 3.11+
- Git
- ~ modest amount of RAM (streaming keeps usage low)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repo-url>
cd projects/PROJ-713-calibration-of-predictive-intervals-for-

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install dependencies
pip install -r requirements.txt
```

> **Note**: `prophet` may need system libraries (`gcc`, `make`, `python3-dev`). On Ubuntu runners they are pre‑installed; on other platforms install the appropriate build tools.

## Data Preparation

The pipeline expects the M4 and UCI Electricity datasets. Because these URLs are **not present in the verified‑datasets list**, the script will first run a **Verified‑Dataset‑Check** (Task **T000a**) that cross‑references the required URLs with the verified list. If the URLs are missing, the run aborts with a clear error explaining how to add them to the verified list. If the check passes, the script proceeds to download the archives from the canonical sources defined in `code/config.yaml`.

```bash
# Verify (and download if missing) the raw data
python code/utils/checksum.py --download
```

The script:
1. Performs the pre‑run verification described above.
2. Downloads each archive.
3. Computes SHA‑256 checksums.
4. Stores the files under `data/raw/`.
5. Writes the checksum values to `state/dataset_hashes.yaml`.

## Running the Benchmark

### Full benchmark (may exceed the 6 h CI limit)
```bash
python code/evaluation/runner.py
```

### Recommended CI‑friendly run (sample of a representative number of series)
```bash
python code/evaluation/runner.py --sample-size 500
```
*`--sample-size` triggers stratified sampling as described in `research.md`.*

## Expected Outputs (found under `results/`)

| File | Description |
|------|-------------|
| `coverage.csv` | Empirical coverage for 0.80 & 0.95 intervals. |
| `distributional_metrics.csv` | PIT KS & Ljung‑Box p‑values, CRPS scores. |
| `significance_test.csv` | Paired bootstrap p‑values. |
| `conformal_results.csv` | Coverage before/after SCCP and improvement delta. |
| `benchmark_timing.csv` | Runtime per stage (useful for CI monitoring). |
| `skipped_series.log` | Log of series skipped due to constant variance or LSTM instability. |
| `contract_validation.log` | Summary of schema validation (Task T026). |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **OOM / MemoryError** | Large single series exceeding RAM | The The loader will automatically down‑sample to an appropriate number of thousand points.; check `logs/loader.log`. |
| **LSTM NaN/Inf intervals** | Numerical instability | The runner retries with a lower learning rate; after two failures the series is logged to `results/skipped_series.log`. |
| **Dataset download fails** | URLs not verified or network issue | Verify that the URLs appear in the verified‑datasets block; add them if missing, then re‑run. |
| **Constitution amendment pending** | T040 not yet approved | Results are still generated; KS test is primary. Once the amendment is merged, the pipeline will automatically prioritize Ljung‑Box if desired. |
| **Schema validation errors** | CSV columns mismatch contracts | Review `contract_validation.log` for details; fix the offending script and re‑run. |

---  