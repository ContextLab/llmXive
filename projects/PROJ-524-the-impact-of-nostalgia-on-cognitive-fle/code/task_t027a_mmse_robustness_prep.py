"""
T027a: MMSE Robustness Data Prep

Reads from data/processed/cleaned_age_filtered.csv (output of T012a).
This dataset has age filtering applied but NO score or MMSE filtering.
Writes this pre-MMSE-exclusion dataset to data/processed/cleaned_dataset_no_mmse.csv.
Ensures data/raw/raw_dataset.csv exists (from T010b) before proceeding.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path

# Setup logging using project utils if available, otherwise standard
try:
    from utils import setup_logging, log_info, log_warning, log_error
except ImportError:
    # Fallback if utils is not in path for direct execution
    logging.basicConfig(level=logging.INFO)
    def log_info(msg): logging.info(msg)
    def log_warning(msg): logging.warning(msg)
    def log_error(msg): logging.error(msg)

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_path = project_root / "data" / "raw" / "raw_dataset.csv"
    age_filtered_path = project_root / "data" / "processed" / "cleaned_age_filtered.csv"
    no_mmse_output_path = project_root / "data" / "processed" / "cleaned_dataset_no_mmse.csv"

    # 1. Verify raw dataset exists (dependency T010b)
    if not raw_data_path.exists():
        log_error(f"ERR_RAW_DATA_MISSING: Required file {raw_data_path} does not exist.")
        raise FileNotFoundError(f"ERR_RAW_DATA_MISSING: {raw_data_path} not found. Ensure T010b has run.")

    log_info(f"Found raw dataset at {raw_data_path}")

    # 2. Verify age filtered dataset exists (dependency T012a)
    if not age_filtered_path.exists():
        log_error(f"ERR_AGE_FILTERED_MISSING: Required file {age_filtered_path} does not exist.")
        raise FileNotFoundError(f"ERR_AGE_FILTERED_MISSING: {age_filtered_path} not found. Ensure T012a has run.")

    log_info(f"Loading age-filtered dataset from {age_filtered_path}")
    df_age_filtered = pd.read_csv(age_filtered_path)

    log_info(f"Loaded {len(df_age_filtered)} records from age-filtered dataset.")

    # 3. Write to cleaned_dataset_no_mmse.csv
    # This file represents the state before MMSE exclusion (and before score exclusion if T012b hasn't run, 
    # but per task description, we read from cleaned_age_filtered which is post-T012a).
    # The task specifically asks to write this to cleaned_dataset_no_mmse.csv.
    no_mmse_output_path.parent.mkdir(parents=True, exist_ok=True)
    df_age_filtered.to_csv(no_mmse_output_path, index=False)

    log_info(f"Successfully wrote pre-MMSE-exclusion dataset to {no_mmse_output_path}")
    log_info(f"Record count: {len(df_age_filtered)}")

    return True

if __name__ == "__main__":
    main()