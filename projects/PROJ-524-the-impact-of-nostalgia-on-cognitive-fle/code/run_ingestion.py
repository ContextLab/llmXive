import os
import sys
import json
import logging
import subprocess
import pandas as pd
from pathlib import Path

from utils import setup_logging, log_info, log_error
from config import get_config, ensure_dirs

def main():
    """
    Execute the ingestion pipeline (T010b).
    This script runs code/ingestion.py to fetch/generate data,
    validates the output schema, and ensures the raw dataset is saved.
    """
    setup_logging()
    config = get_config()
    ensure_dirs()

    log_info("Executing T010b: Running ingestion pipeline...")

    # Execute the ingestion script
    ingestion_script = Path(config['code_dir']) / 'ingestion.py'
    if not ingestion_script.exists():
        log_error(f"Ingestion script not found at {ingestion_script}")
        sys.exit(1)

    try:
        # Run the ingestion script
        result = subprocess.run(
            [sys.executable, str(ingestion_script)],
            check=True,
            capture_output=True,
            text=True
        )
        log_info("Ingestion script execution successful.")
        if result.stdout:
            for line in result.stdout.splitlines():
                log_info(f"  {line}")
        if result.stderr:
            for line in result.stderr.splitlines():
                log_info(f"  {line}")
    except subprocess.CalledProcessError as e:
        log_error(f"Ingestion script failed with return code {e.returncode}")
        if e.stdout:
            log_error(e.stdout)
        if e.stderr:
            log_error(e.stderr)
        sys.exit(1)

    # Validate output artifacts
    raw_dataset_path = Path(config['data_raw_dir']) / 'raw_dataset.csv'
    metadata_path = Path(config['data_raw_dir']) / 'metadata.json'

    if not raw_dataset_path.exists():
        log_error(f"Required output file missing: {raw_dataset_path}")
        sys.exit(1)

    if not metadata_path.exists():
        log_error(f"Required output file missing: {metadata_path}")
        sys.exit(1)

    # Validate schema of raw_dataset.csv
    try:
        df = pd.read_csv(raw_dataset_path)
        required_columns = ['age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            log_error(f"Schema validation failed. Missing columns: {missing_cols}")
            sys.exit(1)
        
        log_info(f"Schema validation passed. Found columns: {list(df.columns)}")
        log_info(f"Total records in raw dataset: {len(df)}")
        
        # Log sample data
        log_info("Sample data (first 3 rows):")
        log_info(df.head(3).to_string())
        
    except Exception as e:
        log_error(f"Failed to read or validate raw dataset: {e}")
        sys.exit(1)

    log_info("T010b completed successfully: raw_dataset.csv generated and validated.")

if __name__ == "__main__":
    main()