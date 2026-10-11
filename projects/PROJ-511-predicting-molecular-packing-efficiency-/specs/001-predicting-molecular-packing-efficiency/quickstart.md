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

# 4. Encode SMILES with the frozen transformer (streaming, CPU‑only, batch size auto‑fallback)
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
- **Primary model performance**: `validation_report.json` shows `spearman_rho ≥ 0.3` **and** Bonferroni‑corrected `p_value ≤ 0.05`, indicating statistical significance at the conventional α = 0.05 level (SC‑002).  
- **Null‑result check**: If `spearman_rho < 0.2`, the report must show `p_value ≥ 0.05` (SC‑003).  
- **Robustness**: Sensitivity table shows variation of `spearman_rho` across thresholds ≤ ±0.05 (SC‑004 is not defined; robustness is captured by the sensitivity analysis).  
- **Runtime**: Full pipeline completes ≤ 6 h on the GitHub Actions free‑tier runner (SC‑005).  

Run the test suite to confirm all unit and integration tests pass:
```bash
pytest tests/
```

## Troubleshooting
| Symptom | Possible Cause | Remedy |
|---------|----------------|--------|
| OOM during `encode_smiles.py` | Batch size too large for available RAM | The script automatically reduces the batch size (64 → 32 → 16) and retries. |
| Few records after filtering | Atom‑count or volume filters too strict | Inspect `data/raw/cod.jsonl` and adjust `--max-atoms` or `--volume-range` parameters. |
| Permutation test takes longer than expected | Inefficient parallelization | Ensure `joblib` is using all available cores; the implementation is optimized to finish within 2 h. |
| Missing COD data | No verified COD URL is supplied | Provide a verified COD mirror URL or adopt an open substitute as described in the Data Availability note. |

---

