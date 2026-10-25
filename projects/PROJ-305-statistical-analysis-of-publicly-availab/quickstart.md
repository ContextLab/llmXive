# Quickstart: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

## Input Provenance

The pipeline analyses Vaccine Adverse Event Reporting System (VAERS) data for
reporting years 2020-2023. The primary input is the verified, publicly
accessible Hugging Face dataset
`chrisvoncsefalvay/vaers-outcomes` (VAERS outcomes, parquet format),
fetched programmatically with the `datasets` library
(`datasets.load_dataset("chrisvoncsefalvay/vaers-outcomes", split="train")`).
The raw file is stored immutably at `data/raw/vaers_2020_2023.parquet` with a
SHA-256 checksum recorded in `data/checksums.txt`. VAERS is operated by the
U.S. FDA and CDC; the data are spontaneous adverse-event reports and carry
the well-known limitations of such systems (no denominators, reporting bias,
no causality assessment).

## Prerequisites

- Python 3.11+
- A Linux/macOS environment (or GitHub Actions runner) with >= 7 GB RAM and
 >= 10 GB free disk space. The pipeline is CPU-only (FR-006).

## Installation

```bash
git clone <REPO_URL>
cd <REPO_NAME>
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r src/requirements.txt
```

## Step‑by‑Step Execution

1. **Create the directory tree and filesystem evidence artifact (T001)**

 ```bash
 python code/setup_project_structure.py
 ```

 Writes `logs/structure.txt` (output of `tree -a -L 3`, with a `find`
 fallback). Verification: `test -s logs/structure.txt`.

2. **Download the VAERS dataset**
 ```bash
 python src/data/download.py
 ```
 - Downloads the verified parquet from
 `chrisvoncsefalvay/vaers-outcomes` and writes
 `data/raw/vaers_2020_2023.parquet` plus its SHA-256 to
 `data/checksums.txt`. Any download failure raises an exception — there is
 no synthetic fallback.

3. **Validate the raw schema**
 ```bash
 python -m src.data.validate --input data/raw/vaers_2020_2023.parquet
 ```
 - Checks required columns (`VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`,
 `REPT_DATE`) against `contracts/dataset.schema.yaml`; writes
 `logs/validate_pass.txt` on success, `logs/validate_fail.txt` and exit 1
 on failure.

4. **Clean, map MedDRA to SOC, and split into analysis groups (T004)**

 ```bash
 python src/data/clean.py
 ```
 - Produces `data/processed/cleaned.parquet` plus per-group parquet files
 (`covid.parquet`, `non_covid.parquet`, `flu.parquet`) and a summary in
 `logs/clean_summary.txt`.

5. **Run the full analysis pipeline (T009)**

 ```bash
 python -m src.main
 ```
 This single runnable command orchestrates:
 - Disproportionality calculations (`output/signals.csv`).
 - Benjamini‑Hochberg correction.
 - Signal flagging (2‑out‑of‑3 rule **plus** BH‑adjusted p‑value < 0.05 **and** hold‑out validation).
 - Temporal profiling (canonical CSV files `output/temporal_profiles/<SOC>.csv`; optional PNG plots).
 - Temporal‑bias robustness check (signals must survive spike‑week removal).
 - Flu‑only sensitivity analysis (`output/sensitivity_analysis.csv`).
 - Memory profiling and final `output/report.md`.

6. **Verify contracts**
 ```bash
 pytest -q tests/contract/
 ```
 All JSON‑schema contracts must pass.

7. **Inspect results**
 - `output/signals.csv` – table of ROR/PRR/IC with adjusted p‑values, hold‑out validation flag, and stability indicator.
 - `output/temporal_profiles/` – CSV files for weekly counts (canonical) and optional PNG plots for the top signals (labelled "Reporting Time").
 - `output/sensitivity_analysis.csv` – Δ‑metrics vs. Flu baseline.
 - `output/report.md` – summary, memory usage, and limitations.

## Troubleshooting

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| `logs/structure.txt` missing | Step 1 not executed | Run `python code/setup_project_structure.py` |
| Download fails | Hugging Face dataset unreachable | Confirm the dataset id `chrisvoncsefalvay/vaers-outcomes` |
| `E_SCHEMA_MISSING` from validate | Required columns absent | Confirm the downloaded parquet matches the contract |
| MemoryError | Dataset larger than 7 GB RAM | Set `USE_CHUNKED=True` in `src/utils/config.py`; the pipeline will process the parquet in 500 k‑row chunks. |
| `logs/structure.txt` missing | Step 1 not executed | Run `python code/setup_project_structure.py` |
| Plot functions raise `ImportError` | Placeholder code in `src/utils/plots.py` not replaced | Ensure the full implementation of `plot_weekly_counts` is present (provided in the repository). |
| Lint failures (`ruff` exit 1) | Style violations | Run `ruff check src/` locally, fix reported issues, then re‑run the lint script. |

## Next Steps
- Review `output/report.md` and incorporate the findings into the manuscript (`paper/`).
- Run the full test suite (`pytest -q`) to ensure ongoing compliance.
- To experiment with a larger VAERS archive, replace the download URL with the full dataset identifier; the same pipeline will handle it provided memory constraints are respected.