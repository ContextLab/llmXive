# Quickstart: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Prerequisites

- Python 3.11 or newer  
- Internet access (for dataset streaming and Materials Project API)  
- Materials Project API key exported as `MP_API_KEY`  
- GitHub Actions‑compatible runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)

## Installation

```bash
# Clone the repository
git clone 
cd PROJ-170-predicting-catalytic-activity

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

**requirements.txt**

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

1. **Create required directories** (the skeleton test expects these):

   ```bash
   python - <<'PY'
import pathlib, os
for sub in ["data/raw", "data/processed", "outputs", "tests/unit", "tests/integration", "tests/contract"]:
    pathlib.Path(sub).mkdir(parents=True, exist_ok=True)
PY
   ```

2. **Download raw data** (OC20 parquet shards and Materials Project descriptors) and verify expected columns:

   ```bash
   python code/download_data.py
   ```

   *Outputs*: `data/raw/oc20_parquet/`, `data/raw/mp_cache.json`, `required_columns.json`, `data/checksums.txt`

3. **Extract electronic descriptors** (no intermediate persisted file; processing is streamed):

   ```bash
   python code/extract_descriptors.py
   ```

4. **Preprocess & align** (impute missing values, scale, produce unified CSV). Because no experimental TOF dataset is currently available, the target column will be left null:

   ```bash
   python code/preprocess.py
   ```

   *Outputs*: `data/processed/aligned_dataset.csv`, `outputs/alignment_metrics.json`, `outputs/scaling_report.json`, `outputs/imputation_log.json`

5. **(Optional) Model training & evaluation**  
   *Only run after an open experimental TOF dataset has been provided.*  
   ```bash
   python code/train.py          # XGBoost
   python code/train_baseline.py
   python code/stat_test.py
   python code/interpret.py
   python code/evaluate_reduced.py
   python code/report.py
   ```

6. **Run the full test suite** (ensures reproducibility, schema compliance, edge‑case handling, runtime (`metrics.json.total_seconds`)):

   ```bash
   pytest -v
   ```

   Expected outcome: all tests pass, confirming that the pipeline up to alignment satisfies the constitution and all FR/SC that are currently realizable.

## Expected Runtime & Resource Usage

- **Total wall‑clock time**: ≤ 2 hours for the alignment‑only pipeline on the standard GitHub Actions runner (SC‑004 limit: ≤ 6 h).  
- **Peak RAM**: ≤ 5 GB (streaming + chunked descriptor extraction).  
- **Disk consumption**: ≤ 12 GB (raw parquet streamed; final CSV a few hundred MB).  

All steps are CPU‑only; no GPU resources are required.

---

