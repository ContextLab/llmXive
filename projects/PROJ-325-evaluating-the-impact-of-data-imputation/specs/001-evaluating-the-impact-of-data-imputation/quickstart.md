# Quickstart: Evaluating the Impact of Data Imputation on Variance Estimation in Public Surveys

## Prerequisites
- Python 3.11+
- `pip`
- 7 GB RAM available (local or CI)

## Installation

1. **Clone & Navigate**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-325-evaluating-the-impact-of-data-imputation
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3. **Verify Environment**:
    ```bash
    python -c "import pandas; import sklearn; import statsmodels; import miceforest; print('Environment OK')"
    ```

## Running the Pipeline

### 1. Data Ingestion (Phase 1)
Downloads and checksums the verified dataset. Replace `<GSS_URL>` and `<ACS_URL>` with the verified URLs once they are available.
```bash
python code/data/loader.py --source "gss" \
  --url "<GSS_URL>" \
  --output data/raw/gss_2018.parquet
python code/data/loader.py --source "acs" \
  --url "<ACS_URL>" \
  --output data/raw/acs_income.parquet
```

### 2. Synthetic Data Generation (Phase 2)
Generates a dataset with known ground truth for validation.
```bash
python code/data/synthetic.py --n-rows 50000 --mechanism "MAR" \
  --output data/processed/synthetic_mar.parquet
```

### 3. Imputation & Variance Calculation (Phase 3)
Runs Complete‑Case, Single Mean, and MICE.
```bash
python code/imputation/run_all.py \
  --input data/processed/synthetic_mar.parquet \
  --methods "cc,single,mice" \
  --mice-chains 4 \
  --mice-iterations 1000 \
  --burn-in 500 \
  --output data/processed/imputation_results.json
```

### 4. Bias Analysis & Sensitivity (Phase 4)
Calculates bias and runs the prescribed sensitivity sweep (`m ∈ {5,10,20}`).
```bash
python code/metrics/bias.py \
  --results data/processed/imputation_results.json \
  --true-variance 150.5 \
  --sweep-param "m" \
  --sweep-values "5,10,20" \
  --output data/reports/bias_analysis.json
```

### 5. Report Generation
Generates the final report with the mandatory associational disclaimer.
```bash
python code/main.py --generate-report --output reports/final_report.md
# The report will contain the footer:
# "All findings are associational; no causal claims are made."
```

## Validation
- Verify that `data/raw/` contains `.sha256` checksum files.  
- Ensure `reports/final_report.md` ends with the required associational footer.  
- Confirm `data/reports/bias_analysis.json` includes `is_pass_sc002` fields for each method.

