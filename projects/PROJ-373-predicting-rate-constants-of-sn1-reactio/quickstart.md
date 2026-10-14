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
Run the full pipeline step‑by‑step or via the main orchestrator.

### Step 1: Atomic Gate (combined ingestion, validation, and download)
```bash
python code/data/atomic_gate.py
```

This command performs all FR‑009 validations, downloads the verified SN1 datasets,
merges them into `data/raw/sn1_raw_merged.parquet`, creates an empty exclusion log
at `data/processed/exclusion_raw.log`, and writes the pipeline status file
`data/processed/.pipeline_status` (OK on success, ABORTED on fatal failure).

### Step 2: Map Columns
```bash
python code/data/mapping.py --input data/raw/sn1_raw_merged.parquet --output data/processed/intermediate_sn1.csv --exclusion-log data/processed/exclusion_raw.log
```

### Step 3: Clean Data
```bash
python code/data/clean.py --input data/processed/intermediate_sn1.csv --output data/processed/cleaned_intermediate.csv --exclusion-log data/processed/exclusion_raw.log
```

### Step 4: Compute Descriptors
```bash
python code/data/descriptors.py --input data/processed/cleaned_intermediate.csv --output data/processed/descriptors.csv --exclusion-log data/processed/exclusion_raw.log
```

### Step 5: Finalize Dataset
```bash
python code/data/finalize_dataset.py \
 --input-path data/processed/cleaned_intermediate.csv \
 --output-path data/processed/cleaned_sn1.csv \
 --exclusion-path data/processed/exclusion_report.csv \
 --success-rate-path data/processed/success_rate.json \
 --checksum-path data/processed/cleaned_sn1.csv.sha256
```

### Step 6: Split Data
```bash
python code/data/split.py --input data/processed/cleaned_sn1.csv --output-dir data/processed/
```

## Verification
After step 1, ensure that:
- `data/raw/sn1_raw_merged.parquet` exists,
- `data/processed/exclusion_raw.log` exists and contains only the header row,
- `data/processed/.pipeline_status` contains the string `OK`.

If any required metadata column is missing from the source datasets,
the script aborts, writes `ABORTED` to the status file, and exits with
code 1.