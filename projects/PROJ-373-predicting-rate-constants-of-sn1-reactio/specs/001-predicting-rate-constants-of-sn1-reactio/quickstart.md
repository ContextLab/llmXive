# Quickstart Guide: Predicting SN1 Rate Constants

## Project Structure
- `code/`: Source code
- `data/`: Data files (raw, processed)
- `tests/`: Test suite
- `specs/`: Specifications and documentation
- `artifacts/`: Model outputs and reports

## Prerequisites
- Python 3.8+
- pip

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution
Run the full pipeline step-by-step or via the main orchestrator.

### Step 1: Schema Check (T011a)
```bash
python code/data/schema_check.py --dataset-name "author/DTS-SN1-15-01-2024" --output data/processed/schema_check.log
```

### Step 2: Download Data (T011b)
```bash
python code/data/download.py --schema-pass --output data/raw/sn1_raw.parquet
```

### Step 3: Map Columns (T011c)
```bash
python code/data/mapping.py --input data/raw/sn1_raw.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log
```

### Step 4: Initialize Exclusion Log (T011d)
```bash
python code/data/init_exclusion_log.py --output data/processed/exclusion_raw.log
```

### Step 5: Clean Data (T012)
```bash
python code/data/clean.py --input data/processed/intermediate_sn1.csv --output data/processed/cleaned_intermediate.csv --exclusion-log data/processed/exclusion_raw.log
```

### Step 6: Compute Descriptors (T013)
```bash
python code/data/descriptors.py --input data/processed/cleaned_intermediate.csv --output data/processed/descriptors.csv --exclusion-log data/processed/exclusion_raw.log
```

### Step 7: Validate Exclusion Log (T013b)
```bash
python code/data/exclusion_report.py --input data/processed/exclusion_raw.log --schema specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml --output data/processed/exclusion_validation.log
```

### Step 8: Aggregate Exclusions (T015)
```bash
python code/data/exclusion_report.py --aggregate --clean-log data/processed/clean.log --raw-log data/processed/exclusion_raw.log --output data/processed/exclusion_report.csv
```

### Step 9: Finalize Dataset (T016)
```bash
python code/data/finalize_dataset.py \
 --input-path data/processed/cleaned_intermediate.csv \
 --intermediate-path data/processed/intermediate_sn1.csv \
 --output-path data/processed/cleaned_sn1.csv \
 --exclusion-path data/processed/exclusion_report.csv \
 --success-rate-path data/processed/success_rate.json \
 --checksum-path data/processed/cleaned_sn1.csv.sha256
```

### Step 10: Split Data (T014)
```bash
python code/data/split.py --input data/processed/cleaned_sn1.csv --output-dir data/processed/
```

## Verification
Check that `data/processed/cleaned_sn1.csv` and `data/processed/success_rate.json` exist and contain valid data.
Ensure `success_rate` in `success_rate.json` is >= 0.95.