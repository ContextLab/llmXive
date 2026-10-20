# Quickstart: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites
* Python 3.11 or newer
* Git
* Network access (only needed to install packages; no external data download is required for the default synthetic run)
* Adequate GB RAM minimum (the full long‑term synthetic dataset fits comfortably)

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

**Verification** – run the helper that confirms the environment:

```bash
python -m code.verify_requirements
# Expected output: a line containing the word "success" in results/requirements_install.log
```

## Run the Full Pipeline (Synthetic Data)

The default pipeline uses a **deterministic synthetic dataset** that fulfills the required schema. This enables end‑to‑end validation of the statistical workflow while being transparent that no real composition measurements are used.

```bash
python -m code.main
```

The script executes the following steps in order (matching the task table in `plan.md`):

1. **Synthetic data generation** (`generate_synthetic_data.py`) – creates `data/raw/synthetic.parquet`.  
2. **Hourly alignment** (`align.py`) – produces `data/processed/aligned_hourly.parquet` **and** `data/artifacts/alignment_report.json`.  
3. **Coupling‑function calculation** (`coupling_functions.py`) – produces `data/processed/with_coupling.parquet`.  
4. **Baseline & full regressions** (`regression.py`) – produce `baseline_model.json` and `full_model.json`.  
5. **ΔR² computation**, **5‑fold cross‑validation**, **block permutation test**, **sensitivity analysis**, **FDR correction**, **VIF calculation**.  
6. **Reporting** – aggregates all results into `data/artifacts/final_report.json` and generates diagnostic plots under `data/artifacts/figures/`.

All artifact files are listed in the table below (automatically created by the pipeline):

| File | Description |
|------|-------------|
| `data/processed/aligned_hourly.parquet` | Hourly‑aligned synthetic dataset (schema‑validated). |
| `data/artifacts/alignment_report.json` | Summary of alignment offsets and gap handling. |
| `data/processed/with_coupling.parquet` | Dataset with ε and Newell coupling function columns. |
| `baseline_model.json` | Coefficients, p‑values, R² for the baseline model. |
| `full_model.json` | Same for the full model (includes composition ratios). |
| `delta_r2.json` | Incremental R² and bootstrap confidence interval. |
| `cv_metrics.json` | Mean out‑of‑sample R² for baseline & full models (5‑fold TimeSeriesSplit). |
| `permutation_results.json` | Null distributions, p‑values for each composition coefficient. |
| `sensitivity.json` | Results of the α‑sweep {0.01, 0.05, 0.10} with BH‑FDR correction. |
| `final_report.json` | Consolidated JSON report with provenance and all metrics. |
| `figures/` | PNG/PDF plots (correlation heatmap, coefficient bar chart, residual diagnostics). |

## Testing

```bash
pytest tests/
```

The test suite checks:

* I/O helpers work with and without `pyarrow`.  
* Synthetic generation produces a file that validates against `contracts/dataset.schema.yaml`.  
* Alignment respects the ≤ 30 min offset rule and correctly flags rows with composition gaps > 6 h (they become `null`).  
* Coupling‑function formulas match the definitions in the research document.  
* Regression scripts write files with the exact names required by the plan.  
* End‑to‑end pipeline creates all expected artifacts.

## Optional Real‑Data Path (Not Currently Available)

If an open source providing ACE SWICS or WIND composition ratios becomes available, replace step 1 with:

```bash
python -m code.ingestion.download_real --start 2000-01-01 --end 2020-12-31
```

The downstream scripts (`align.py`, `coupling_functions.py`, etc.) will operate unchanged on the downloaded data.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `ImportError: pyarrow` when reading parquet | `pyarrow` not installed | The I/O helper automatically falls back to `fastparquet`; ensure `fastparquet` is installed (it is pinned in `requirements.txt`). |
| MemoryError during regression | Attempting to load a much larger dataset than the synthetic one | Verify you are using the synthetic dataset (default). If you switched to a real dataset, consider sampling or streaming. |
| Schema validation failed | Missing required column or wrong type | Run `python -m code.utils.io validate data/processed/aligned_hourly.parquet` to see detailed errors; the schema is `contracts/dataset.schema.yaml`. |
| “No open composition source found” printed by `download_real.py` | Expected – there is currently no verified open composition dataset. | Continue with the synthetic pipeline; no further action needed. |

## Re‑run Quickly on a Subset (for debugging)

```bash
python -m code.main --quick  # uses only the initial segment of rows.
```

All downstream steps respect the subset automatically.

---


