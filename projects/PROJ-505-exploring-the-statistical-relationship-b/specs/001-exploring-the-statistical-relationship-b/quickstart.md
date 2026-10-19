# Quickstart: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites
* Python 3.11 or newer
* Git
* Access to a GitHub Actions runner **or** a local Linux/macOS environment with ≥ 4 GB RAM
* Network access to NASA CDAWeb (for real data download)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd projects/PROJ-505-exploring-the-statistical-relationship-b

# 2️⃣ Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r requirements.txt
```

**Verification step** – after installing, you can run the helper script that checks the requirement installation and produces a log:

```bash
python -m code.verify_requirements
```

The script writes `results/requirements_install.log`. A successful run contains the word `success`.

Every non‑comment line of `requirements.txt` is pinned as
`package==major.minor.*` (e.g. `pyspedas==1.6.*`), which guarantees
reproducible installs. The old non‑conforming `pyarrow>=15.0.0` line has
been replaced by `pyarrow==15.0.*` plus a `fastparquet==2024.*` fallback
engine, so Parquet I/O works even when `pyarrow` is unavailable.

## Data Preparation (REAL data — no synthetic fallback)

All input data are REAL measurements obtained from NASA CDAWeb via the
`pyspedas` package:

* **ACE SWICS** ion composition (O, Fe, He, H, C charge‑state fluxes)
* **WIND SMS/STICS** ion composition
* **OMNI hourly** bulk parameters, IMF, and the Dst / Kp geomagnetic indices

```bash
# Download the real raw data (writes data/raw/ace_swics/,
# data/raw/wind_sms/, data/raw/omni/ and data/raw/checksums.yaml)
python code/ingestion/download_real.py --start 2000-01-01 --end 2020-12-31
```

On resource‑limited CI runners (where the full 20‑year fetch exceeds
the execution time budget), a **verified REAL 1‑year sample** of the
same CDAWeb sources is fetched instead — the identical command with a
1‑year window:

```bash
python code/ingestion/download_real.py --start 2000-01-01 --end 2000-12-31
```

This is a real subsample of the same archives (sample size and period
are recorded in `data/raw/checksums.yaml`), never synthetic data. The
loader **fails loudly** (raises `ConnectionError`/`RuntimeError`) if any
fetch fails — there is no synthetic fallback anywhere in the pipeline.

## Run the Full Analysis Pipeline

```bash
python -m code.main
```

`main.py` executes the full pipeline in dependency order on the real data:

1. Real‑data ingestion (`code/ingestion/download_real.py`) — ACE SWICS + WIND SMS + OMNI
2. Alignment (`code/ingestion/align.py`) → `data/processed/aligned_hourly.parquet`
3. Coupling‑function calculation (`code/analysis/coupling_functions.py`) → `data/processed/with_coupling.parquet`
4. Baseline & full regressions (`code/analysis/regression.py`)
5. ΔR² computation and 5‑fold time‑series cross‑validation
6. Block permutation test (max 10 000 iterations)
7. Percentile significance, Benjamini–Hochberg FDR, and threshold sensitivity
8. Final report aggregation → `data/artifacts/final_report.json`

A quick end‑to‑end smoke run on a 1‑year real subset is available via:

```bash
python -m code.main --quick
```

All results are written to `data/artifacts/`:

| File | Content |
|------|---------|
| `aligned_hourly.parquet` | One row per hour, hourly‑median aligned real data |
| `baseline_model.json`, `full_model.json` | Regression coefficients, SEs, p‑values, R² |
| `delta_r2.json`, `delta_r2_ci.json` | Incremental R² and 95 % bootstrap CI |
| `cv_metrics.json` | Out‑of‑sample R² (baseline & full, 5‑fold TimeSeriesSplit) |
| `permutation_results.json` | Null distributions, two‑sided p‑values |
| `fdr_results.csv` | BH‑FDR‑corrected p‑values |
| `sensitivity.json`, `threshold_stability.csv` | Threshold sweep {0.01, 0.05, 0.10} |
| `final_report.json` | Aggregated report with provenance and runtime |
| `figures/` | Correlation heatmap, coefficient plots, residual diagnostics |

**Interpretation**: All numbers are real measurements from CDAWeb archives
for 2000–2020. Findings are observational/associational.

## Testing

```bash
pytest tests/
```

The test suite checks:

* I/O helpers (`code/utils/io.py`) work with and without `pyarrow` (fastparquet fallback).
* Real‑data download fails loudly on fetch errors (no synthetic fallback).
* Raw CDF files exist for ACE SWICS / WIND SMS / OMNI, checksums match,
  and parsed CDF variables include the composition species and Dst/Kp
  (skipped automatically when the raw cache is empty on an offline runner).
* Schema compliance of the aligned parquet file against `contracts/dataset.schema.yaml`.
* Correctness of coupling‑function formulas (hand‑computed ε and Newell values).
* End‑to‑end pipeline produces all expected artifact files.

## Verification of Requirements Installation

After installing the dependencies you can run the verification helper:

```bash
python -m code.verify_requirements
```

It will re‑run `pip install -r requirements.txt` and write
`results/requirements_install.log`. The presence of the word `success`
in that log confirms that the pinned requirements install without error.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `ImportError: pyarrow` when saving parquet | `pyarrow` not installed on the runner | The I/O helper automatically falls back to the `fastparquet` engine; ensure `fastparquet==2024.*` is installed (`pip install -r requirements.txt`). |
| `ConnectionError` during download | CDAWeb unreachable or dataset ID changed | Fix network access / dataset ID and re‑run `code/ingestion/download_real.py`. The pipeline intentionally does NOT fall back to synthetic data. |
| MemoryError during regression | Loading more than the compute budget allows | Process the real data in chunks or a fixed‑seed real subsample (documented in the run report); never substitute synthetic data. |
| "Schema validation failed" | Aligned file missing a required column | Re‑run `python code/ingestion/download_real.py` then `python -m code.main`. |
