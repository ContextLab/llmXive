"""
T012: Download OpenNeuro datasets and verify variable fit.

Fetches ds003104 (and ds if specified) from OpenNeuro.
Verifies metadata for 'wcst_perseverative_errors' and 'age >= 50'.
Outputs parquet files to data/raw/ with checksums.
"""
import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import requests
from tqdm import tqdm

# Add project root to path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.logging_config import get_logger, log_data_transition, log_exclusion_reason

# Configuration
DATASETS = ["ds003104"]  # Primary dataset for WCST/Aging
# Fallback/Secondary if needed, but ds003104 is the primary target for WCST
# OpenNeuro API base
OPENNEURO_API = "https://api.openneuro.org"

# Output paths
DATA_RAW_DIR = Path("data/raw")
LOG_DIR = Path("logs")

# Required variables for variable-fit check
REQUIRED_BEHAVIORAL_COLS = ["wcst_perseverative_errors"]
MIN_AGE = 50

def setup_logger():
    logger = get_logger("download_data")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def calculate_file_checksum(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset_metadata(dataset_id):
    """Fetch dataset metadata from OpenNeuro GraphQL API."""
    query = """
    query GetDataset($datasetId: ID!) {
        dataset(id: $datasetId) {
            id
            title
            description
            snapshot {
                id
                summary
                derivatives
            }
        }
    }
    """
    url = f"{OPENNEURO_API}/gitlab/v1/graphql"
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "variables": {"datasetId": dataset_id}}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("dataset")
    except requests.exceptions.RequestException as e:
        logger = setup_logger()
        logger.error(f"Failed to fetch metadata for {dataset_id}: {e}")
        return None

def download_dataset_files(dataset_id, output_dir):
    """
    Download dataset files from OpenNeuro.
    Since OpenNeuro does not provide a direct 'download all' JSON endpoint for behavioral data
    in a single call without parsing BIDS structure, we simulate the download by:
    1. Checking if the dataset exists.
    2. Attempting to fetch the 'participants.tsv' which contains demographic and behavioral data.
    
    Note: In a full BIDS pipeline, one would use bids-validator or dandi-api.
    Here we target the specific behavioral file.
    """
    logger = setup_logger()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # We will attempt to fetch the participants.tsv from the latest snapshot
    # OpenNeuro URL pattern for raw files: https://openneuro.org/datasets/{id}/files
    # But for direct download, we often need the git hash or specific snapshot.
    # Strategy: Try to get the 'participants.tsv' directly if the dataset is public.
    # If direct download fails, we might need to parse the BIDS structure.
    
    # For ds003104, the data is public.
    # URL pattern for specific file in a snapshot:
    # https://openneuro.org/datasets/{dataset_id}/files/{file_id} -> download
    # Or use the s3 bucket if available.
    
    # Simplified approach for this task:
    # 1. Try to download participants.tsv from the public git repo or s3 if known.
    # 2. If not directly downloadable via simple GET, we will construct a mock of the 
    #    *structure* but fetch REAL data if possible.
    #    However, OpenNeuro's public API for raw file download usually requires a snapshot tag.
    
    # Let's try to get the latest snapshot ID first.
    # GraphQL query for snapshots
    query = """
    query GetSnapshots($datasetId: ID!) {
        dataset(id: $datasetId) {
            snapshots {
                id
                tags
            }
        }
    }
    """
    url = f"{OPENNEURO_API}/gitlab/v1/graphql"
    headers = {"Content-Type": "application/json"}
    payload = {"query": query, "variables": {"datasetId": dataset_id}}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        snapshots = response.json().get("data", {}).get("dataset", {}).get("snapshots", [])
        if not snapshots:
            logger.error(f"No snapshots found for {dataset_id}")
            return False
        
        # Use the latest snapshot
        latest_snapshot = snapshots[0] # Usually sorted by date
        snapshot_id = latest_snapshot["id"]
        logger.info(f"Using snapshot: {snapshot_id}")
        
        # Construct URL for participants.tsv
        # OpenNeuro file listing API: /gitlab/v1/datasets/{id}/files?recursive=true
        # Or direct download: /gitlab/v1/datasets/{id}/files/{path}
        # We need the path relative to the dataset root.
        
        # Let's try to fetch the file listing to find participants.tsv
        files_url = f"{OPENNEURO_API}/gitlab/v1/datasets/{dataset_id}/files?recursive=true"
        # Note: OpenNeuro API might require specific headers or authentication for file listing
        # If public, it should work.
        
        # Alternative: Use the s3 bucket if we can infer it (often public)
        # ds003104 -> s3://openneuro/ds003104/
        s3_base = f"https://openneuro.s3.amazonaws.com/{dataset_id}"
        # This is a common pattern but not guaranteed by the API spec.
        
        # Robust approach: Use the OpenNeuro Python client if available, or fallback to direct S3.
        # Since we can't assume extra deps beyond requirements.txt (which includes requests),
        # we will try the S3 direct link for ds003104 as it is a known public dataset.
        
        # Target file: participants.tsv
        tsv_path = "participants.tsv"
        s3_url = f"{s3_base}/{tsv_path}"
        
        logger.info(f"Attempting to download {tsv_path} from {s3_url}")
        
        response = requests.get(s3_url, stream=True)
        if response.status_code == 200:
            local_file = output_dir / f"{dataset_id}_{tsv_path}"
            with open(local_file, 'wb') as f:
                for chunk in tqdm(response.iter_content(chunk_size=8192), desc=f"Downloading {dataset_id}"):
                    f.write(chunk)
            logger.info(f"Downloaded {local_file}")
            
            # Convert to parquet for the task output
            df = pd.read_csv(local_file, sep='\t')
            parquet_file = output_dir / f"{dataset_id}_behavioral.parquet"
            df.to_parquet(parquet_file, index=False)
            logger.info(f"Saved parquet: {parquet_file}")
            
            # Calculate checksum
            checksum = calculate_file_checksum(local_file)
            checksum_file = output_dir / f"{dataset_id}_checksum.txt"
            with open(checksum_file, 'w') as f:
                f.write(f"{checksum}  {local_file.name}\n")
            logger.info(f"Saved checksum: {checksum_file}")
            
            return True
        else:
            logger.error(f"Failed to download {tsv_path} from S3. Status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing {dataset_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_variable_fit(df, dataset_id):
    """
    Check metadata for required columns and age criteria.
    Returns (is_valid, reason).
    """
    logger = setup_logger()
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_BEHAVIORAL_COLS if col not in df.columns]
    if missing_cols:
        reason = f"Missing required columns: {missing_cols}"
        logger.error(f"[DATASET_VARIABLE_MISMATCH] {dataset_id}: {reason}")
        log_exclusion_reason(dataset_id, "DATASET_VARIABLE_MISMATCH", reason)
        return False, reason
    
    # Check age distribution
    if 'age' in df.columns:
        valid_ages = df[df['age'] >= MIN_AGE]
        if len(valid_ages) == 0:
            reason = f"No participants with age >= {MIN_AGE}"
            logger.error(f"[DATASET_VARIABLE_MISMATCH] {dataset_id}: {reason}")
            log_exclusion_reason(dataset_id, "DATASET_VARIABLE_MISMATCH", reason)
            return False, reason
        logger.info(f"Found {len(valid_ages)} participants with age >= {MIN_AGE}")
    else:
        # If age is not in participants.tsv, it might be in a separate file, 
        # but for this task we assume it's in the main behavioral file.
        # If missing, we cannot verify the age constraint, so we fail the variable fit check strictly.
        reason = "Age column not found to verify age >= 50 constraint"
        logger.warning(f"[DATASET_VARIABLE_MISMATCH] {dataset_id}: {reason}")
        # Depending on strictness, we might fail. The task says "Verify variable fit".
        # If we can't verify, we should halt or warn. Let's fail to be safe.
        log_exclusion_reason(dataset_id, "DATASET_VARIABLE_MISMATCH", reason)
        return False, reason

    return True, "Variable fit verified"

def main():
    logger = setup_logger()
    logger.info("Starting T012: Download OpenNeuro datasets")
    
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    
    for dataset_id in DATASETS:
        logger.info(f"Processing dataset: {dataset_id}")
        
        # 1. Download data
        if not download_dataset_files(dataset_id, DATA_RAW_DIR):
            logger.error(f"Skipping {dataset_id} due to download failure.")
            continue
        
        # 2. Load and verify
        parquet_path = DATA_RAW_DIR / f"{dataset_id}_behavioral.parquet"
        if not parquet_path.exists():
            logger.error(f"Parquet file not found for {dataset_id}")
            continue
        
        df = pd.read_parquet(parquet_path)
        
        is_valid, reason = verify_variable_fit(df, dataset_id)
        
        if not is_valid:
            # The task says: "If missing, halt with 'DATASET_VARIABLE_MISMATCH' error"
            # We log it and continue to next dataset if any, or fail the script.
            logger.critical(f"Halting processing for {dataset_id} due to variable mismatch.")
            # We do not delete the file, but we mark it as invalid in a log.
            # The task output is the parquet file, but the validity is logged.
            # If the dataset is invalid, we might want to exclude it from further pipeline steps.
            # For this task, we output the file but log the error.
            # However, the task says "If missing, halt...". We halt this dataset's processing.
            continue
        
        log_data_transition(
            source=f"OpenNeuro/{dataset_id}",
            destination=str(parquet_path),
            record_count=len(df),
            details="Variable fit verified"
        )
        success_count += 1
    
    if success_count == 0:
        logger.error("No datasets successfully processed.")
        sys.exit(1)
    
    logger.info(f"T012 completed. {success_count} datasets processed successfully.")

if __name__ == "__main__":
    main()
