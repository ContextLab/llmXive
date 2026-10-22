# Quickstart: Simulated Social Rejection → Behavioral Proxies

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (or a local runner with ≥ 7 GB RAM)

## Installation

```bash
# 1️⃣ Clone the repository
git clone <repository-url>
cd PROJ-258-the-effect-of-simulated-social-rejection

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

### Step 1 – Ingest the Cyberball dataset
```bash
python code/ingest.py \
 --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" \
 --out-dir data/raw \
 --dataset-id ds000208
```
*Outputs*:
- `data/raw/ds000208.parquet`
- `data/raw/metadata.json` (SHA‑256 checksum, download timestamp)
- `data/raw/CITATION.md`
- `data/interim/reward_unavailable.json` (placeholder indicating no reward data)

### Step 2 – Validate the download
```bash
python code/validate.py \
 --raw data/raw/ds000208.parquet \
 --schema contracts/dataset.schema.yaml \
 --output data/interim/ingest_validation_report.json
```
*Outputs*: JSON validation report. The script exits 1 on any schema violation.

### Step 3 – Preprocess
```bash
python code/preprocess.py \
 --input data/raw/ds000208.parquet \
 --output data/processed/analysis_ready_ds000208.csv
```
*Outputs*:
- `data/processed/analysis_ready_ds000208.csv` (cleaned, outlier‑flagged, Z‑score normalized)
- `data/interim/outlier_log.json` (per‑condition IQR thresholds & counts)

### Step 4 – Statistical Analysis
```bash
python code/analyze.py \
 --data data/processed/analysis_ready_ds000208.csv \
 --output results/analysis_output.json
```
*Outputs*: `results/analysis_output.json` containing **design‑aware** ANOVA results, FDR‑corrected p‑values, effect sizes, and α‑sensitivity flags.

### Step 5 – Outlier Sensitivity Check
```bash
python code/analyze.py \
 --data data/processed/analysis_ready_ds000208.csv \
 --outlier-sensitivity results/outlier_sensitivity.json
```
*Outputs*: Comparison of statistics with vs. removed outliers.

### Step 6 – Generate Report
```bash
python code/report.py \
 --input results/analysis_output.json \
 --output paper/report.md \
 --results-output results/analysis_results.json
```
*Outputs*: `paper/report.md` and `results/analysis_results.json`.

### Step 7 – Verify Everything (CI style)
```bash
pytest tests/
```
All tests must pass. They enforce:
- Schema compliance for raw, processed, and analysis files.
- Correct FDR inequality (`p_fdr >= p_raw`).
- Presence of required phrasing constraints in the final report.
- Execution time ≤ 6 h.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| **Missing columns** | Dataset version mismatch | Verify the URL points to the verified parquet file; re‑run `ingest.py`. |
| **Memory overflow** | Dataset larger than RAM budget | `ingest.py` will halt; you cannot proceed until a smaller dataset is used. |
| **Design not selected** | Unexpected condition values | Ensure both “rejection” and “control” appear in the `condition` column. |
| **Assumption violations** | Normality or homogeneity failures | Pipeline will automatically switch to Welch’s ANOVA or Kruskal‑Wallis. |
| **“causal” appears in report** | Manual edit of `paper/report.md` | Regenerate the report; the script enforces the phrasing rule. |