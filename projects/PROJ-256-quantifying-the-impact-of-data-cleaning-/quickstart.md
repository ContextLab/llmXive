# Quickstart Guide: Quantifying the Impact of Data Cleaning

## Prerequisites
- Python 3.11+
- Dependencies installed via `pip install -r requirements.txt`

## Execution Steps

### 1. Ensure Data Exists
```bash
python code/t011_ensure_data.py
```

### 2. Run Baseline Analysis (T012)
Downloads/loads raw data and computes baseline statistics.
```bash
python code/t012_run_baseline_analysis.py
```
*Output: `data/processed/baseline_metrics.json`*

### 3. Record Baseline Metrics (T013)
Formats and validates baseline metrics.
```bash
python code/t013_record_baseline_metrics.py
```
*Output: `data/processed/baseline_metrics.json` (updated)*

### 4. Clean Data (T017-T022)
Applies cleaning strategies.
```bash
python code/t022_save_cleaned_datasets.py
```
*Output: `data/processed/dataset_cleaned_*.csv`*

### 5. Re-analyze Cleaned Data (T023)
Computes statistics on cleaned variants.
```bash
python code/t023_reanalyze_cleaned_variants.py
```
*Output: `data/processed/cleaned_metrics.json`*

### 6. Generate Reports (T027-T041)
Compares metrics and generates visualizations.
```bash
python code/t041_generate_final_report.py
```
*Output: `data/processed/final_report.txt`, `figures/*.png`*

## Validation
Run the validation script to ensure all artifacts are present.
```bash
python code/run_quickstart_validation.py
```