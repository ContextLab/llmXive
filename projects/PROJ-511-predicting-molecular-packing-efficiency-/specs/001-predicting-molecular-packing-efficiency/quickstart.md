# Quickstart: Predicting Molecular Packing Efficiency

## Prerequisites
* Python 3.11 or newer  
* `pip` (installed with Python)  
* Internet access to download the COD dataset **once a verified URL is supplied** (see Data Availability note below).  

## Installation
```bash
# Navigate to the project root
cd projects/PROJ-511-predicting-molecular-packing-efficiency-

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline
> **Important** – The pipeline cannot start until a verified COD dataset URL is provided (see Data Availability section). Once the source is available, the steps below will run end‑to‑end on a fresh GitHub Actions runner.

### Step 1: Data Acquisition & Feature Engineering (Phase 0)
```bash
# 1. Download and filter COD entries (organic ≤ 50 non‑H atoms)
python code/download_cod.py --output data/raw/cod.jsonl

# 2. Extract or generate SMILES
python code/generate_smiles.py \
    --input data/raw/cod.jsonl \
    --output data/processed/with_smiles.csv

# 3. Compute 3‑D geometry descriptors and confounder counts
python code/compute_descriptors.py \
    --input data/processed/with_smiles.csv \
    --output data/processed/with_descriptors.csv

# 4. Encode SMILES with the frozen transformer (streaming)
python code/encode_smiles.py \
    --input data/processed/with_descriptors.csv \
    --output data/processed/full_feature_matrix.csv
```

### Step 2: Model Training (Phase 2)
```bash
python code/train_model.py \
    --data data/processed/full_feature_matrix.csv \
    --model-primary data/artifacts/model_primary.pt \
    --model-full data/artifacts/model_full.pt
```

### Step 3: Evaluation & Reporting (Phases 3‑5)
```bash
# Evaluation (metrics, permutation test, VIF, residual analysis)
python code/evaluate_model.py \
    --model data/artifacts/model_primary.pt \
    --data data/processed/full_feature_matrix.csv \
    --output data/artifacts/validation_report.json

# Sensitivity analysis over high‑packing thresholds
python code/sensitivity_analysis.py \
    --model data/artifacts/model_primary.pt \
    --data data/processed/full_feature_matrix.csv \
    --output data/artifacts/sensitivity_results.json

# Generate the final HTML report
python code/report_generator.py \
    --validation data/artifacts/validation_report.json \
    --output data/artifacts/report.html
```

## Verification Checklist
- **Dataset size**: `full_feature_matrix.csv` contains **≥ 500** rows (SC‑001).  
- **Primary model performance**: `validation_report.json` shows `spearman_rho ≥ 0.3` **and** Bonferroni‑corrected `p_value ≤ 0.05` (SC‑002).  
- **Null‑result check**: If `spearman_rho < 0.2`, the report must show `p_value ≥ 0.05` (SC‑003).  
- **Robustness**: Sensitivity table shows variation of `spearman_rho` across thresholds ≤ ±0.05 (SC‑004).  
- **Runtime**: Full pipeline completes ≤ 6 h on the GitHub Actions free tier (SC‑005).  
- **Permutation‑test deviation**: If the 4‑hour timeout fires, `validation_report.json` records `actual_shuffles` and logs the deviation (SC‑006).  

Run the test suite to confirm all unit and integration tests pass:
```bash
pytest tests/
```

## Troubleshooting
| Symptom | Possible Cause | Remedy |
|---------|----------------|--------|
| OOM during `encode_smiles.py` | Batch size too large for available RAM | Reduce `--batch-size` (default setting) or let the automatic Kaggle GPU escape hatch handle it. |
| A relatively small number of records after filtering. | Atom‑count or volume filters too strict | Inspect `data/raw/cod.jsonl` and adjust `--max-atoms` or `--volume-range` parameters. |
| Permutation test logs a timeout | CPU resources insufficient for a large number of shuffles | Accept the logged `actual_shuffles` (≥ 1 000) and note the deviation in the report (SC‑006). |
| Missing COD data | No verified COD URL supplied | Provide a verified COD mirror URL or revise the scope to an open crystallographic dataset. |

---

