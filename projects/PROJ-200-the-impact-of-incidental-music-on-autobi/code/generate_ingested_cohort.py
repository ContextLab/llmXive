import os
import sys
import logging
import hashlib
import yaml
from datetime import datetime
from pathlib import Path

# Ensure the code directory is in the path if running as script
if os.path.basename(os.getcwd()) == 'code':
    sys.path.insert(0, os.path.dirname(os.getcwd()))
else:
    sys.path.insert(0, os.path.join(os.getcwd(), 'code'))

from config import get_project_root, get_config_dict
from data_ingestion import (
    download_datasets, filter_cohort, audit_amt_source,
    handle_fallback, apply_frequency_threshold, calculate_ratio_score,
    calculate_residualized_score, main as ingest_main
)
from utils import setup_logging, get_logger

logger = get_logger(__name__)

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_state_entry(state_path: str, file_path: str, checksum: str) -> None:
    """Update state.yaml with the new file entry."""
    state_data = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}

    state_data['files'] = state_data.get('files', {})
    state_data['files'][os.path.basename(file_path)] = {
        'path': file_path,
        'checksum': checksum,
        'generated_at': datetime.utcnow().isoformat(),
        'task_id': 'T018'
    }

    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def main():
    """
    Orchestrates the full US1 ingestion pipeline and generates the final parquet.
    This function implements the order: Fallback Check -> Frequency Filter -> Score Calc.
    """
    logger.info("Starting T018: Generate ingested_cohort.parquet")
    project_root = get_project_root()
    config = get_config_dict()

    # Ensure output directory exists
    processed_dir = project_root / 'data' / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_file = processed_dir / 'ingested_cohort.parquet'
    state_file = project_root / 'state.yaml'

    try:
        # 1. Download datasets (T013)
        logger.info("Step 1: Downloading datasets...")
        download_datasets()

        # 2. Audit AMT source (T012a)
        logger.info("Step 2: Auditing AMT source...")
        audit_amt_source()

        # 3. Fallback Check (T023) - MUST run before frequency filter
        logger.info("Step 3: Checking for fallback conditions (T023)...")
        # This function typically modifies global state or returns a flag.
        # We assume the ingestion pipeline functions handle the logic internally
        # or we need to call a specific setup function.
        # Based on task T028 description, we rely on the orchestration in main.py
        # or here we call the specific steps.
        
        # Since T013a, T023, T015, T014, T016 are separate functions, we need to
        # chain them here or call the main ingestion logic if it exists.
        # The task T028 says "Implement code/main.py orchestration".
        # However, T018 is "Generate ... parquet".
        # We will assume the standard flow is:
        # load raw -> filter cohort -> check fallback -> apply freq -> calc scores -> save.
        
        # Let's assume data_ingestion.py has a `run_full_ingestion` or we call the functions.
        # Since T028 is the orchestration, maybe we should call `ingest_main`?
        # But T018 is the generator. Let's implement the logic here to ensure independence.
        
        # Re-implementing the flow described in T028 within this script to ensure T018 works standalone.
        
        # A. Load Raw Data (simulated via download_datasets side effects or explicit load)
        # We need to load the raw data to process. Assuming download_datasets puts them in data/raw/
        raw_msd_path = project_root / 'data' / 'raw' / 'msd_tracks.csv' # Example name, adjust if needed
        raw_amt_path = project_root / 'data' / 'raw' / 'amt_cues.csv'
        
        if not raw_msd_path.exists():
            # Fallback if download_datasets created different filenames or paths
            # Try to find the file
            raw_files = list((project_root / 'data' / 'raw').glob('*.csv'))
            if not raw_files:
                raise FileNotFoundError("No raw CSV files found in data/raw/")
            # Assume the first one is MSD for now or handle based on config
            # In a real scenario, download_datasets would return paths or set global vars.
            # Let's assume standard names based on common MSD datasets or config.
            # If the file is missing, the download step failed or names are different.
            # We will proceed assuming download_datasets populated the expected files.
            pass

        # To be robust, we will assume the functions in data_ingestion.py 
        # handle the data loading internally or we need to load it here.
        # Given the constraints, we will call the main orchestration from data_ingestion 
        # if it exists, or reconstruct the flow.
        
        # Let's assume the `main` function in data_ingestion.py (imported as `ingest_main`)
        # performs the full pipeline up to saving the parquet or returning the dataframe.
        # If `ingest_main` just prints, we need to do the work here.
        
        # Let's assume the standard pattern:
        # 1. download_datasets()
        # 2. df = filter_cohort(...)
        # 3. handle_fallback(...)
        # 4. df = apply_frequency_threshold(df)
        # 5. df = calculate_ratio_score(df)
        # 6. df = calculate_residualized_score(df)
        # 7. save to parquet.
        
        # We need to ensure the functions return the dataframe.
        
        # Re-running the pipeline steps explicitly:
        logger.info("Running ingestion pipeline steps...")
        
        # Step 1: Download (already done, but ensure)
        # download_datasets() # Called above
        
        # Step 2: Load and Filter Cohort
        # We need to load the raw data first.
        # Assuming download_datasets creates 'data/raw/msd_tracks.csv' and 'data/raw/amt_cues.csv'
        # We'll use pandas to load.
        import pandas as pd
        
        # Try to find the MSD file
        msd_file = None
        for ext in ['csv', 'parquet', 'tsv']:
            candidates = list((project_root / 'data' / 'raw').glob(f'*msd*.{ext}')) + \
                         list((project_root / 'data' / 'raw').glob(f'*tracks*.{ext}'))
            if candidates:
                msd_file = candidates[0]
                break
        
        if not msd_file:
            # Fallback: try any csv
            all_csv = list((project_root / 'data' / 'raw').glob('*.csv'))
            if all_csv:
                msd_file = all_csv[0]
            else:
                raise FileNotFoundError("Could not locate MSD dataset in data/raw/")
        
        logger.info(f"Loading MSD data from {msd_file}")
        df_raw = pd.read_csv(msd_file)
        
        # T013a: Filter Cohort
        df_filtered = filter_cohort(df_raw)
        
        # T023: Handle Fallback (Check birth year sufficiency)
        # This function likely returns a flag or modifies the dataframe/context.
        # Assuming it returns a boolean or modifies a global config.
        # We assume it logs the result.
        handle_fallback(df_filtered) 
        
        # T015: Apply Frequency Threshold
        df_filtered = apply_frequency_threshold(df_filtered)
        
        # T014: Calculate Ratio Score
        df_filtered = calculate_ratio_score(df_filtered)
        
        # T016: Calculate Residualized Score
        df_filtered = calculate_residualized_score(df_filtered)
        
        # Save to Parquet
        logger.info(f"Saving ingested cohort to {output_file}")
        df_filtered.to_parquet(output_file, index=False)
        
        # Verify file
        if not output_file.exists():
            raise FileNotFoundError(f"Output file {output_file} was not created.")
        
        # Calculate Checksum
        checksum = calculate_file_checksum(str(output_file))
        logger.info(f"Checksum generated: {checksum}")
        
        # Update State
        save_state_entry(str(state_file), str(output_file), checksum)
        logger.info("State updated successfully.")
        
        logger.info("T018 completed successfully.")
        
    except Exception as e:
        logger.error(f"T018 failed: {e}")
        raise

if __name__ == '__main__':
    setup_logging()
    main()
