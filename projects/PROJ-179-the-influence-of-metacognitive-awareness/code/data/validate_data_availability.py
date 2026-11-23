import os
import sys
import logging
import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_FIELDS = ["confidence_rating", "source_label"]
BLOCKING_DATASET_ID = "ds003386"

def get_project_root() -> Path:
    """Returns the project root directory."""
    return paths.root

def is_dataset_valid(file_path: Path) -> bool:
    """
    Checks if a CSV file contains the required behavioral fields
    and that they are not entirely empty.
    """
    try:
        # Read only the header first to check columns
        df_header = pd.read_csv(file_path, nrows=0)
        cols = df_header.columns.tolist()
        
        if not all(field in cols for field in REQUIRED_FIELDS):
            return False
        
        # Check a small sample to ensure fields aren't just empty strings or NaNs
        df_sample = pd.read_csv(file_path, nrows=100)
        for field in REQUIRED_FIELDS:
            if df_sample[field].isnull().all() or (df_sample[field].astype(str).str.strip() == "").all():
                return False
        
        return True
    except Exception as e:
        log.debug(f"Could not validate {file_path}: {e}")
        return False

def main():
    """
    Orchestrates the data availability validation gate.
    
    Logic:
    1. Search data/raw for CSV files.
    2. If any CSV is valid (contains required fields), exit 0.
    3. If no valid CSVs found, check if ds003386 is the only source.
    4. If ds003386 is the only source, exit 1 with specific error.
    5. Otherwise, exit 1 with general block message.
    """
    raw_dir = paths.data("raw")
    
    if not raw_dir.exists():
        log.error("Data directory 'data/raw' does not exist. Project blocked.")
        sys.exit(1)

    csv_files = list(raw_dir.glob("*.csv"))
    all_files = list(raw_dir.iterdir())

    if not csv_files:
        log.error("No CSV files found in data/raw. Project blocked.")
        sys.exit(1)

    # 1. Check for any valid behavioral dataset
    valid_files = [f for f in csv_files if is_dataset_valid(f)]
    
    if valid_files:
        log.info(f"Success: Valid behavioral dataset found: {valid_files[0].name}")
        sys.exit(0)

    # 2. No valid dataset found. Check if the source is strictly the blocking structural MRI dataset.
    # We detect ds003386 by checking if the ID appears in any filename in the raw directory.
    is_ds003386_present = any(BLOCKING_DATASET_ID in f.name.lower() for f in all_files)
    
    # If ds003386 is present and no other non-ds003386 files exist, or if it's the only source
    # we trigger the specific blocking error required by the task.
    non_blocking_files = [f for f in all_files if BLOCKING_DATASET_ID not in f.name.lower()]
    
    if is_ds003386_present and not non_blocking_files:
        log.error(f"ERROR: Project blocked. OpenNeuro {BLOCKING_DATASET_ID} lacks required behavioral fields. Aborting.")
        sys.exit(1)
    
    # 3. Fallback: Search results for other datasets already on disk
    log.info("Searching for alternative datasets in data/raw...")
    for f in csv_files:
        log.info(f"Checked {f.name}: missing or empty required fields {REQUIRED_FIELDS}")

    log.error("No valid behavioral dataset containing 'confidence_rating' and 'source_label' found. Project remains blocked.")
    sys.exit(1)

if __name__ == "__main__":
    main()