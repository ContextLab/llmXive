# Quickstart: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Prerequisites

- Python 3.11 or newer
- Internet access (for dataset streaming and MP API)
- Materials Project API key set as environment variable `MP_API_KEY`
- GitHub Actions‑compatible runner (2 CPU cores, ≤7 GB RAM, ≤14 GB disk)

## Installation

```bash
# Clone the repository (assume you are already in the project root)
git clone https://github.com/your-org/PROJ-170-predicting-catalytic-activity.git
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

1. **Create directory skeleton** (required for integration tests):

   ```bash
   python - <<'PY'
import pathlib
for sub in ["data/raw", "data/processed", "outputs", "tests/unit", "tests/integration", "tests/contract"]:
    pathlib.Path(sub).mkdir(parents=True, exist_ok=True)
PY
   ```

2. **Download data** (raw OC20, MP descriptors) and verify columns:

   ```bash
   python code/download_data.py
   ```

   *Outputs*: `data/raw/oc20_parquet/`, `data/raw/mp_cache.json`, `required_columns.json`

3. **Extract electronic descriptors** (no intermediate persisted file):

   ```bash
   python code/extract_descriptors.py
   ```

4. **Preprocess & align** (impute, scale, generate `aligned_dataset.csv` and related logs):

   ```bash
   python code/preprocess.py
   ```

   *Outputs*: `data/processed/aligned_dataset.csv`, `outputs/alignment_metrics.json`, `outputs/alignment_failure.json`, `outputs/imputation_log.json`, `outputs/scaling_report.json`

5. **Train models & evaluate** (nested CV with outer hold‑out):

   ```bash
   python code/train.py
   ```

   *Outputs*: `code/models/best_xgboost.json`, `outputs/best_params.json`, `outputs/metrics.json`, `outputs/normality_test.json`, `outputs/statistical_test.json`

6. **Reduced‑model verification (SC‑003)**:

   ```bash
   python code/evaluate_reduced.py
   ```

   *Outputs*: `outputs/reduced_model_metrics.json`

7. **Interpretability (SHAP)**:

   ```bash
   python code/interpret.py
   ```

   *Outputs*: `outputs/shap_rankings.csv`, `outputs/shap_barplot.png`

8. **Generate final report**:

   ```bash
   python code/report.py
   ```

   *Output*: `outputs/final_report.md`

9. **Run the test suite** (ensures directory existence, schema compliance, edge‑case handling):

   ```bash
   pytest -v
   ```

   Expected outcome: all tests pass, confirming reproducibility and constitutional compliance.

## Expected Runtime & Resource Usage

- **Total wall‑clock time**: ≤ 3 hours on the standard GitHub Actions runner (SC‑004 limit: ≤ 6 h).  
- **Peak RAM**: ≤ 5 GB (due to streaming and chunked descriptor extraction).  
- **Disk consumption**: ≤ 12 GB (raw parquet shards are streamed; only processed CSV (a few hundred MB) remains).  

All steps are CPU‑only; no GPU resources are required.  

