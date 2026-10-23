# Quickstart: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Prerequisites
- **Python 3.11+** installed locally or in the CI runner.  
- **Internet access** (required for streaming OC20 and calling the Materials Project API).  
- **Materials Project API key** exported as an environment variable: `export MP_API_KEY=YOUR_KEY`.  
- **GitHub Actions runner constraints** (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk) – the pipeline is designed to respect these limits.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd PROJ-170-predicting-catalytic-activity

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

**`requirements.txt` (pinned versions)**

```text
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2
xgboost==2.0.2
shap==0.44.0
datasets==2.14.6
matplotlib==3.8.2
seaborn==0.13.0
pytest==7.4.3
pymatgen==2023.10.1
mp-api==0.35.0
tqdm==4.66.2
```

## Step‑by‑Step Execution

All scripts are located under `code/`. Each script writes its outputs to the paths described in `data-model.md`.

1. **Create directory skeleton** (required for the test suite):

   ```bash
   python - <<'PY'
import pathlib
for sub in [
    "data/raw",
    "data/processed",
    "outputs",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]:
    pathlib.Path(sub).mkdir(parents=True, exist_ok=True)
PY
   ```

2. **Download raw data & fetch MP descriptors**  
   This step streams OC20 and caches MP descriptors; it also writes `required_columns.json` and `data/checksums.txt`.

   ```bash
   python code/download_data.py
   ```

3. **Compute DFT‑derived descriptors** (real physics, not placeholders):

   ```bash
   python code/extract_descriptors.py
   ```

   *Output*: `data/processed/oc20_descriptors.parquet` containing all required descriptor columns.

4. **Alignment, imputation, scaling** (produces the unified CSV). Because we do not yet have an open experimental TOF dataset, the `experimental_tof` column will be `null`.

   ```bash
   python code/preprocess.py
   ```

   *Outputs*: `data/processed/aligned_dataset.csv`, `outputs/alignment_metrics.json`, `outputs/scaling_report.json`, `outputs/imputation_log.json`.

5. **Scope‑revision request (handles missing TOF data)**  
   Generates a JSON request and a placeholder CSV with a correctly formatted checksum (no trailing newline).

   ```bash
   python code/request_scope_revision.py
   ```

   *Outputs*: `outputs/scope_revision_request.json`, `data/raw/experimental_tof_placeholder.csv`, updated `data/checksums.txt`.

6. **(Optional) Model training & evaluation** – run **only after** an open experimental TOF dataset is supplied.

   ```bash
   python code/train.py            # XGBoost grid‑search
   python code/train_baseline.py  # Linear baseline
   python code/stat_test.py       # Shapiro‑Wilk + paired test
   python code/interpret.py       # SHAP analysis
   python code/evaluate_reduced.py
   python code/report.py
   ```

7. **Run the full test suite** (verifies schema compliance, checksum integrity, and runtime ≤ 6 h):

   ```bash
   pytest -v
   ```

   Expected outcome: **all tests pass**; `metrics.json.total_seconds` ≤ 21600.

## Expected Runtime & Resource Usage
- **Alignment‑only pipeline** (steps 1‑4) completes in **≈ 1 hour** on the CI runner.  
- **Peak RAM** stays below **5 GB** thanks to streaming and chunked processing.  
- **Disk consumption** ≤ 12 GB (raw parquet shards streamed, final CSV ~200 MB).  
- All steps are **CPU‑only**; no GPU resources are required.

## What to Do When the Experimental TOF Dataset Becomes Available
1. Replace `data/raw/experimental_tof_placeholder.csv` with the real CSV (same header).  
2. Update `data/checksums.txt` with the new SHA‑256 hash (single‑line, no newline).  
3. Re‑run `code/preprocess.py` to fill the `experimental_tof` column.  
4. Proceed with steps 6 above to train, evaluate, and report.

---
