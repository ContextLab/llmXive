# Quickstart: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Input Provenance
This pipeline utilizes the Vaccine Adverse Event Reporting System (VAERS) data, specifically the 2020-2023 CSV archives provided by the CDC (Centers for Disease Control and Prevention) through their official public data repository. [UNRESOLVED-CLAIM: c_b655bdcb — status=not_enough_info]

## Prerequisites
- Python 3.11+
- Git (to clone the repository)
- Access to a GitHub Actions runner **or** a local Linux/macOS environment with ≥ 7 GB RAM and ≥ 10 GB free disk space.

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd <REPO_NAME>

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r src/requirements.txt
```

## Step‑by‑Step Execution

1. **Create directory tree & verification log**
 ```bash
 python -m code.create_structure
 ```
 *`logs/structure.txt` is required for verification task T001.*

2. **Download the VAERS dataset**
 ```bash
 python src/data/download.py
 ```
 - Downloads the official 2020‑2023 VAERS CSV zip archives.
 - Writes SHA‑256 checksums to `data/checksums.txt`.

3. **Validate the raw schema**
 ```bash
 python -m src.data.validate
 ```
 - Exits with `E_SCHEMA_MISSING` if any of `VAX_TYPE`, `SOC_CODE`, `REPT_DATE` are absent.

4. **Clean, map, and split the data**
 ```bash
 python src/data/clean.py
 ```
 - Produces `data/processed/cleaned.parquet` with three groups (`COVID-related`, `Non-COVID-Non-Flu`, `Flu-only`).

5. **Run the full analysis pipeline**
 ```bash
 python -m src.main
 ```
 This orchestrates:
 - Disproportionality calculations (`output/signals.csv`)
 - Benjamini‑Hochberg correction
 - Signal flagging (2‑out‑of‑3 rule)
 - Temporal profiling (plots in `output/temporal_profiles/`)
 - Flu‑only sensitivity analysis (`output/sensitivity_analysis.csv`)
 - Memory profiling and final `output/report.md`.

6. **Verify contracts**
 ```bash
 pytest -q tests/contract/
 ```
 All JSON‑schema contracts must pass.

7. **Inspect results**
 - `output/signals.csv` – table of ROR/PRR/IC with adjusted p‑values.
 - `output/temporal_profiles/` – PNG plots for the top signals.
 - `output/sensitivity_analysis.csv` – Δ‑metrics vs. Flu baseline.
 - `output/report.md` – human‑readable summary, memory usage, and limitations.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---------|--------------|--------|
| `E_SCHEMA_MISSING` from `validate.py` | Required columns absent in the downloaded parquet | Confirm the dataset URL; if missing, request a different verified VAERS source or abort. |
| MemoryError | Dataset larger than 7 GB RAM | Set `USE_CHUNKED=True` in `src/utils/config.py` and re‑run. |
| `logs/structure.txt` missing | Step 1 not executed or `tree` not installed | Run `python -m code.create_structure`. |
| Plot functions raise `ImportError` | `src/utils/plots.py` placeholder not replaced | Ensure the full implementation of `plot_weekly_counts` and `plot_signal_table` exists. |
| Lint failures (`code/run_lint.py` exit 1) | Style violations | Run `ruff check src/` locally and fix reported issues. |