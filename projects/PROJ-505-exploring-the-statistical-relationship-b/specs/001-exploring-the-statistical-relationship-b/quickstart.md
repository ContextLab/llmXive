# Quickstart: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

## Prerequisites
* Python 3.11+  
* Git  
* Network access (only for downloading the open bulk/geomagnetic files; synthetic composition requires no external download)  
* Minimum ≈ a few GB RAM (the full synthetic dataset fits comfortably)

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

## Run the Full Pipeline (Synthetic Composition – Validation Only)

The default pipeline uses a **deterministic synthetic composition dataset** that satisfies the required schema while being transparent that no real composition measurements are used. The pipeline will automatically **abort before any composition‑dependent analysis** if Principle VI has not been formally amended.

```bash
python -m code.main
```

The script executes the steps listed in `plan.md`:

| Step | Description | Output (example) |
|------|-------------|------------------|
| 1️⃣ Synthetic composition generation | `generate_synthetic_composition.py` | `data/raw/synthetic_composition.parquet` |
| 2️⃣ Bulk & geomagnetic download (open sources) | `download_bulk.py` | `data/raw/ace_bulk.csv` & `data/raw/noaa_geomagnetic.parquet` |
| 3️⃣ Checksum creation | `checksum.py` | `data/raw/checksums.yaml` |
| 4️⃣ Hourly alignment | `align.py` | `data/processed/aligned_hourly.parquet` + `alignment_report.json` |
| 5️⃣ Coupling‑function calculation | `coupling_functions.py` | `data/processed/with_coupling.parquet` |
| 6️⃣ Baseline regression | `regression.py --mode baseline` | `baseline_model.json` |
| 7️⃣ Full regression *(conditional)* | `regression.py --mode full` | `full_model.json` (only if real composition & amendment) |
| 8️⃣ ΔR² computation *(conditional)* | `regression.py --compute-delta` | `delta_r2.json` |
| 9️⃣ k‑fold cross‑validation | `cross_validation.py` | `cv_metrics.json` |
| 🔟 Block permutation test *(conditional)* | `permutation_test.py` | `permutation_results.json` |
| 1️⃣1️⃣ Sensitivity & FDR *(conditional)* | `sensitivity.py` | `sensitivity.json` |
| 1️⃣2️⃣ Reporting | `main.py` aggregates everything | `final_report.json` + `figures/` |
| 1️⃣3️⃣ Verification | `pytest tests/` | Test suite results |

All artifact files are listed in `data/artifacts/` and are validated against `contracts/dataset.schema.yaml`.

## Optional Real‑Data Path (Future)

When an open source providing ACE SWICS or WIND composition ratios becomes available, replace step 1 with:

```bash
python -m code.ingestion.download_real_composition --start 2000-01-01 --end 2020-12-31 --output data/raw/real_composition.parquet
```

The downstream scripts (`align.py`, `coupling_functions.py`, etc.) will operate unchanged on the downloaded data, and the pipeline will proceed through the full composition‑dependent analysis.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| `ImportError: pyarrow` when reading parquet | `pyarrow` not installed | The I/O helper automatically falls back to `fastparquet`; ensure `fastparquet` is present (pinned in `requirements.txt`). |
| MemoryError during regression | Attempting to load a much larger dataset than the synthetic one | Verify you are using the synthetic dataset (default). If you switched to a real composition dataset, consider sampling or streaming. |
| Schema validation failed | Missing required column or wrong type | Run `python -m code.utils.io validate data/processed/aligned_hourly.parquet` to see detailed errors; the schema is `contracts/dataset.schema.yaml`. |
| Alignment report shows > 30 % missing composition values | 2‑hour cadence leads to many hourly gaps | This is expected; the report records missing‑value statistics; statistical power may be reduced but the pipeline still runs. |
| “Permutation test exit = 1” | Bug in `permutation_test.py` (e.g., block size larger than data) | Ensure the aligned dataset contains at least 24 hours of data; the script will automatically reduce block size if necessary. |
| “No open composition source found” printed by `download_real_composition.py` | Expected – no verified open composition dataset exists yet | Continue with the synthetic pipeline; no further action needed. |

## Quick Debug Run on a Subset

```bash
python -m code.main --quick   # processes only the initial subset of rows for rapid debugging
```

All downstream steps respect the subset automatically.

--- 