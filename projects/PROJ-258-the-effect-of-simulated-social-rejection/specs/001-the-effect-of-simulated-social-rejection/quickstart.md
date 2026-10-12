# Quickstart: The Effect of Simulated Social Rejection on Positive Feedback

## Prerequisites
- Python 3.11 or newer  
- Git  
- Access to GitHub Actions (or a local runner with ≥ 7 GB RAM)

## Installation

```bash
# 1️⃣ Clone the repository
git clone 
cd PROJ-258-the-effect-of-simulated-social-rejection

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

### Step 1 – Ingest the dataset
```bash
python code/ingest.py \
  --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" \
  --out-dir data/raw \
  --dataset-id ds000208
```
*Outputs*:  
- `data/raw/ds000208.parquet`  
- `data/raw/metadata.json` (checksum, timestamp)  
- `data/raw/CITATION.md` (official dataset citation)  
- Updated `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml`  

*Failure*: Exit code 1 if required columns are missing, if the file size exceeds 7 GB, or if the `condition` column lacks both “rejection” and “control”.

### Step 2 – Preprocess
```bash
python code/preprocess.py \
  --input data/raw/ds000208.parquet \
  --output data/processed/analysis_ready_ds000208.csv
```
*Outputs*:  
- `data/processed/analysis_ready_ds000208.csv` (cleaned, outlier‑flagged, Z‑score normalized)  
- `data/interim/outlier_log.json` (per‑condition IQR thresholds & counts)  

*Failure*: Exit code 1 if memory usage exceeds 7 GB.

### Step 3 – Statistical Analysis
```bash
python code/analyze.py \
  --data data/processed/analysis_ready_ds000208.csv \
  --output results/analysis_output.json
```
*Outputs*: `results/analysis_output.json` containing ANOVA (or ANCOVA) results, FDR‑corrected p‑values, effect sizes, and α‑sensitivity flags.  

*Failure*: Exit code 1 if the design selection logic cannot determine a valid design (should not happen with the single dataset).

### Step 4 – Outlier Sensitivity Check
```bash
python code/analyze.py \
  --data data/processed/analysis_ready_ds000208.csv \
  --outlier-sensitivity results/outlier_sensitivity.json
```
*Outputs*: Comparison of statistics with vs. removed outliers (T017).

### Step 5 – Generate Report
```bash
python code/report.py \
  --analysis results/analysis_output.json \
  --outlier-sensitivity results/outlier_sensitivity.json \
  --design data/interim/design_branch.json \
  --output paper/report.md
```
*Outputs*: `paper/report.md` with (a) design type, (b) statistical tables (or non‑parametric equivalents), (c) FDR‑corrected p‑values, (d) Limitations paragraph containing the exact word **“associational”**, (e) no occurrence of the word **“causal”** in the Results section, and (f) a statement that neural responses are inferred from behavioral proxies.

### Step 6 – Verify Everything (CI style)
```bash
pytest tests/
```
All tests must pass. They enforce:
- Schema compliance for raw, processed, and analysis files.  
- Correct FDR inequality (`p_fdr >= p_raw`).  
- Presence of the required phrasing constraints in the final report.  
- Execution time ≤ 6 h (enforced by T013).

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **Missing columns** (`participant_id`, `condition`, `reaction_time`, `mood_rating`) | Dataset version mismatch | Verify the URL points to the verified parquet file; re‑run `ingest.py`. |
| **Memory overflow** | Dataset larger than a few gigabytes of RAM | `ingest.py` will have halted; you cannot proceed until a smaller dataset is used. |
| **Design not selected** | Unexpected condition values | Ensure both “rejection” and “control” appear in the `condition` column. |
| **Assumption violations** | Normality or homogeneity failures | The pipeline will automatically switch to Kruskal‑Wallis and note this in the report. |
| **“causal” appears in report** | Manual edit of `paper/report.md` | Regenerate the report; the script enforces the phrasing rule. |
| **CITATION.md missing** | Ingestion step skipped | Re‑run `ingest.py`; it creates `CITATION.md`. |
| **Outlier impact unclear** | Need to assess sensitivity | Run Step 4 to produce the outlier‑sensitivity summary. |

---


