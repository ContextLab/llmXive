# Quickstart: The Effect of Simulated Social Rejection on Positive Feedback

## Prerequisites
- Python 3.11 or newer
- Git
- Access to GitHub Actions (or a local runner with ≥ 7 GB RAM)

## Installation

```bash
# 1️⃣ Clone the repository
git clone https://github.com/your-org/PROJ-258-the-effect-of-simulated-social-rejection.git
cd PROJ-258-the-effect-of-simulated-social-rejection

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

### Step 1 – Ingest the datasets
```bash
# Rejection (Cyberball) dataset
python code/ingest.py \
  --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" \
  --out-dir data/raw \
  --dataset-id ds000208

# Reward (Positive‑Feedback) dataset
python code/ingest.py \
  --url "https://huggingface.co/datasets/openneuro/ds003392/resolve/main/data.parquet" \
  --out-dir data/raw \
  --dataset-id ds003392
```
*Outputs*: `data/raw/ds000208.parquet`, `data/raw/ds003392.parquet`, updated `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml` with checksums, and `data/raw/CITATION.md` containing proper dataset citations.  
*Failure*: Exit code 1 if required columns are missing, combined size > 7 GB, or conditions are absent (FR‑001).

### Step 2 – Preprocess
```bash
python code/preprocess.py \
  --input data/raw/ds000208.parquet \
  --output data/processed/analysis_ready_ds000208.csv

python code/preprocess.py \
  --input data/raw/ds003392.parquet \
  --output data/processed/analysis_ready_ds003392.csv
```
*Outputs*: cleaned CSVs (`analysis_ready_*.csv`), `data/interim/outlier_log.json`, and `data/interim/features_<dataset_id>.csv`.  
*Failure*: Exit code 1 if outlier processing exceeds memory limits (FR‑002).

### Step 3 – Statistical Analysis
```bash
python code/analyze.py \
  --rejection data/processed/analysis_ready_ds000208.csv \
  --reward data/processed/analysis_ready_ds003392.csv \
  --output results/analysis_output.json
```
*Outputs*: `results/analysis_output.json` (ANOVA/ANCOVA, FDR, sensitivity).  
*Failure*: Exit code 1 if design selection fails (e.g., missing overlap report).

### Step 4 – Generate Report
```bash
python code/report.py \
  --analysis results/analysis_output.json \
  --output paper/report.md
```
*Outputs*: `paper/report.md` containing the required “associational” phrase in Limitations and no occurrence of “causal” in Results (FR‑003).

### Step 5 – Verify Everything (CI style)
```bash
pytest tests/
```
All tests must pass; they enforce schema compliance, the correct FDR inequality (`p_fdr >= p_raw`), and the phrasing constraints.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **Missing columns** (`participant_id`, `condition`, `reaction_time`, `mood_rating`) | Dataset version mismatch | Ensure the URL points to the verified parquet file; re‑run `ingest.py`. |
| **Memory overflow** | Dataset larger than 7 GB RAM | `ingest.py` will have halted; obtain a smaller subset or choose a different open dataset. |
| **Design not selected** | One of the conditions absent | Verify that both `rejection`/`control` rows exist in ds000208 and that `reward` rows exist in ds003392. |
| **“causal” appears in report** | Manual edit of `paper/report.md` | Regenerate the report; the script enforces the phrasing rule. |
| **CITATION.md missing** | Ingestion step skipped for one dataset | Re‑run `ingest.py` for the missing dataset; it creates `CITATION.md`. |

---



