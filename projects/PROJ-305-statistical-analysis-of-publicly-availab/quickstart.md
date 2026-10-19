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

## Step-by-Step Execution

1. **Create the directory tree and filesystem evidence artifact (T001)**

 ```bash
 python code/create_structure.py
 ```

 Writes `logs/structure.txt` (output of `tree -a -L 3`, with a `find`
 fallback). Verification: `test -s logs/structure.txt`.

2. **Download the VAERS dataset (T002)**

 ```bash
 python src/data/download.py
 ```

 Fetches the verified parquet from Hugging Face
 (`chrisvoncsefalvay/vaers-outcomes`) and writes
 `data/raw/vaers_2020_2023.parquet` plus its SHA-256 to
 `data/checksums.txt`. Any download failure raises an exception — there is
 no synthetic fallback.

3. **Validate the raw schema (T003)**

 ```bash
 python -m src.data.validate --input data/raw/vaers_2020_2023.parquet
 ```

 Checks required columns (`VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`,
 `REPT_DATE`) against `contracts/dataset.schema.yaml`; writes
 `logs/validate_pass.txt` on success, `logs/validate_fail.txt` and exit 1
 on failure.

4. **Clean, map MedDRA to SOC, and split into analysis groups (T004)**

 ```bash
 python src/data/clean.py
 ```

 Produces `data/processed/cleaned.parquet` plus per-group parquet files
 (`covid.parquet`, `non_covid.parquet`, `flu.parquet`) and a summary in
 `logs/clean_summary.txt`.

5. **Run the full analysis pipeline (T009)**

 ```bash
 python -m src.main
 ```

 This single runnable command orchestrates: download -> validate ->
 clean -> disproportionality metrics (ROR/PRR/IC with Benjamini-Hochberg
 correction, `output/signals.csv`) -> bootstrap empirical FDR
 (`output/empirical_fdr.txt`) -> Flu-only sensitivity analysis
 (`output/sensitivity_analysis.csv`) -> weekly reporting-time profiles
 (`output/temporal_profiles/`) -> independent output validation ->
 final report (`output/report.md`), with peak-memory profiling recorded in
 `data/results/memory_profile.json` (abort if > 7 GB).

6. **Run the test suite**

 ```bash
 pytest -q tests/
 ```

7. **Inspect results**

 - `output/signals.csv` — ROR/PRR/IC with 95% CIs and BH-adjusted p-values.
 - `output/temporal_profiles/` — weekly count CSVs and PNGs for top signals
 (labelled "Reporting Time", never "Post-Vaccination Time").
 - `output/sensitivity_analysis.csv` — delta metrics vs. Flu-only baseline.
 - `output/report.md` — summary, memory usage, and limitations.

## Troubleshooting

| Symptom | Likely cause | Remedy |
|---------|--------------|--------|
| `logs/structure.txt` missing | Step 1 not executed | Run `python code/create_structure.py` |
| Download fails | Hugging Face dataset unreachable | Confirm the dataset id `chrisvoncsefalvay/vaers-outcomes`; the script fails loudly rather than falling back to synthetic data |
| `E_SCHEMA_MISSING` from validate | Required columns absent | Confirm the downloaded parquet matches the contract |
| MemoryError | Dataset exceeds 7 GB RAM | Enable chunked processing in `src/utils/config.py` |
| Lint failures | Style violations | Run `ruff check src/` and fix reported issues |