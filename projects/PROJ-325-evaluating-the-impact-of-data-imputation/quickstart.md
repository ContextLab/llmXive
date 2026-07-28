# Quickstart Guide: Evaluating the Impact of Data Imputation

This guide outlines the steps to run the full analysis pipeline.
Ensure you are in the project root directory.

## Prerequisites

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Environment Setup**:
 Ensure `data/raw`, `data/processed`, and `state` directories exist.
 ```bash
 mkdir -p data/raw data/processed state figures
 ```

## Execution Steps

### Step 1: Fetch GSS Data
Download the GSS 2018 subset. Replace `<GSS_URL>` with the actual verified URL.
```bash
python code/data/loader.py --source "gss" --url "<GSS_URL>" --output data/raw/gss_2018_subset.csv
```

### Step 2: Fetch ACS Data (Optional)
Download the ACS income dataset. Replace `<ACS_URL>` with the actual verified URL.
```bash
python code/data/loader.py --source "acs" --url "<ACS_URL>" --output data/raw/acs_income.parquet
```

### Step 3: Generate Synthetic Data
Create a synthetic dataset with MAR missingness for validation.
```bash
python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output data/processed/synthetic_mar_v1.csv
```
*Note: This command also generates `data/processed/synthetic_mar_v1_meta.json`.*

### Step 4: Run Imputation Pipeline
Execute the full imputation comparison (Complete Case, Single Mean, MICE).
```bash
python code/imputation/run_all.py \
 --input data/processed/synthetic_mar_v1.csv \
 --methods "cc,single,mice" \
 --mice-chains 4 \
 --mice-iterations 1000 \
 --burn-in 500 \
 --output data/processed/imputation_results.json
```

### Step 5: Calculate Bias Metrics
Analyze the bias of imputation methods against ground truth.
```bash
python code/metrics/bias.py \
 --results data/processed/imputation_results.json \
 --true-variance 150.5 \
 --sweep-param "m" \
 --sweep-values "5,10,20" \
 --output data/reports/bias_analysis.json
```

### Step 6: Generate Final Report
Compile all results into the final markdown report.
```bash
python code/main.py --generate-report --output reports/final_report.md
```

## Verification

After running the pipeline, verify the outputs:
- Check `data/raw/gss_2018_subset.csv` exists.
- Check `data/processed/synthetic_mar_v1.csv` and `.json` exist.
- Check `data/processed/imputation_results.json` exists.
- Check `data/processed/baseline_results.json` exists.
- Check `reports/final_report.md` exists.

Run the validation script:
```bash
python code/validate_schemas.py
```
