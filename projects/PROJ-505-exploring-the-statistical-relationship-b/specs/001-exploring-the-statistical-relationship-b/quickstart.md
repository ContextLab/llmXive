# Quickstart: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites
* Python 3.11 or newer  
* Git  
* Network access (only for installing packages; the default run uses synthetic data, so no external download is required)  
* Minimum ≈ 2 GB RAM (the full synthetic dataset fits comfortably)

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

## Run the Full Pipeline (Synthetic Composition)

The default pipeline uses a **deterministic synthetic composition dataset** that satisfies the required schema while being transparent that no real composition measurements are used.

```bash
python -m code.main
```

The script executes the steps listed in `plan.md`:

| Step | Description | Output (example) |
|------|-------------|------------------|
| 1️⃣ Synthetic composition generation | `generate_synthetic_composition.py` | `data/raw/synthetic_composition.parquet` |
| 2️⃣ Bulk & geomagnetic download (open sources) | `download_bulk.py` | `data/raw/bulk_and_geomagnetic.parquet` |
| 3️⃣ Hourly alignment | `align.py` | `data/processed/aligned_hourly.parquet` + `alignment_report.json` |
| 4️⃣ Coupling‑function calculation | `coupling_functions.py` | `data/processed/with_coupling.parquet` |
| 5️⃣ Baseline regression | `regression.py --mode baseline` | `baseline_model.json` |
| 6️⃣ Full regression | `regression.py --mode full` | `full_model.json` |
| 7️⃣ ΔR² computation | `regression.py --compute-delta` | `delta_r2.json` |
| 8️⃣ 5‑fold cross‑validation | `cross_validation.py` | `cv_metrics.json` |
| 9️⃣ Block permutation test | `permutation_test.py` | `permutation_results.json` |
| 🔟 Sensitivity & FDR | `sensitivity.py` | `sensitivity.json` |
| 1️⃣1️⃣ Reporting | `main.py` aggregates everything | `final_report.json` + `figures/` |

All artifact files are listed in `data/artifacts/` and are validated against `contracts/dataset.schema.yaml`.

## Testing

```bash
pytest tests/
```

The test suite checks:

* I/O helpers work with and without `pyarrow`.  
* Synthetic generation produces a file that validates against the dataset schema.  
* Alignment respects the ≤ 30 min offset rule and correctly flags rows with composition gaps > 6 h.  
* Coupling‑function formulas match the definitions in `research.md`.  
* Regression scripts write files with the exact names required by the plan.  
* End‑to‑end pipeline creates all expected artifacts.

## Optional Real‑Data Path (Future)

When an open source providing ACE SWICS or WIND composition ratios becomes available, replace step 1 with:

```bash
python -m code.ingestion.download_real_composition --start 2000-01-01 --end 2020-12-31 --output data/raw/real_composition.parquet
```

The downstream scripts (`align.py`, `coupling_functions.py`, etc.) will operate unchanged on the downloaded data.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `ImportError: pyarrow` when reading parquet | `pyarrow` not installed | The I/O helper automatically falls back to `fastparquet`; ensure `fastparquet` is installed (pinned in `requirements.txt`). |
| MemoryError during regression | Attempting to load a much larger dataset than the synthetic one | Verify you are using the synthetic dataset (default). If you switched to a real dataset, consider sampling or streaming. |
| Schema validation failed | Missing required column or wrong type | Run `python -m code.utils.io validate data/processed/aligned_hourly.parquet` to see detailed errors; the schema is `contracts/dataset.schema.yaml`. |
| “No open composition source found” printed by `download_real_composition.py` | Expected – no verified open composition dataset exists yet | Continue with the synthetic pipeline; no further action needed. |
| “Alignment report shows > 30 % missing composition values” | 2‑hour cadence leads to many hourly gaps | This is expected; the report records missing‑value statistics; statistical power may be reduced but the pipeline still runs. |

## Quick Debug Run on a Subset

```bash
python -m code.main --quick   # processes only the first 10 000 rows for rapid debugging
```

All downstream steps respect the subset automatically.

---
