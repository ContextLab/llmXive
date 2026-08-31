import json
import hashlib
import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from datasets import load_dataset, get_dataset_config_names, get_dataset_split_names

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
README_PATH = DATA_DIR / "README.md"
EXCLUSION_LOG_PATH = PROCESSED_DIR / "exclusion_log.json"
BLOCKED_STATUS_PATH = DATA_DIR / "blocked_status.json"
DATASET_IDS_PATH = DATA_DIR / "dataset_ids.txt"

class ChecksumError(Exception):
    """Raised when a checksum verification fails."""
    pass

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_dataset_ids(filepath: Path) -> List[Dict[str, Any]]:
    """
    Parse dataset_ids.txt.
    Expected format: id,source,type (e.g., 42277,openml,time_perception)
    Returns list of dicts: [{'id': '42277', 'source': 'openml', 'type': 'time_perception'}, ...]
    """
    if not filepath.exists():
        logger.error(f"Dataset IDs file not found: {filepath}")
        return []

    datasets = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            if len(parts) >= 2:
                datasets.append({
                    'id': parts[0].strip(),
                    'source': parts[1].strip().lower(),
                    'type': parts[2].strip() if len(parts) > 2 else 'unknown'
                })
            else:
                logger.warning(f"Skipping malformed line in dataset_ids.txt: {line}")
    return datasets

def fetch_openml_dataset(dataset_id: str) -> Optional[Path]:
    """
    Fetch dataset from OpenML using the datasets library.
    Returns path to downloaded dataset or None if failed.
    """
    try:
        logger.info(f"Fetching OpenML dataset {dataset_id}...")
        # Load dataset directly into memory, then save to a temporary parquet/arrow file
        # Note: OpenML datasets in HuggingFace datasets are often under 'openml' with the ID as config
        ds = load_dataset('openml', str(dataset_id), split='train')
        
        # Create a unique filename
        safe_id = str(dataset_id).replace('/', '_')
        output_path = RAW_DIR / f"openml_{safe_id}.parquet"
        
        # Save to parquet for efficient reading later
        ds.to_parquet(str(output_path))
        logger.info(f"Saved OpenML dataset to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset {dataset_id}: {e}")
        return None

def fetch_huggingface_dataset(dataset_id: str) -> Optional[Path]:
    """
    Fetch dataset from HuggingFace Hub.
    Returns path to downloaded dataset or None if failed.
    """
    try:
        logger.info(f"Fetching HuggingFace dataset {dataset_id}...")
        ds = load_dataset(dataset_id, split='train')
        
        safe_id = dataset_id.replace('/', '_')
        output_path = RAW_DIR / f"hf_{safe_id}.parquet"
        
        ds.to_parquet(str(output_path))
        logger.info(f"Saved HuggingFace dataset to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to fetch HuggingFace dataset {dataset_id}: {e}")
        return None

def validate_checksum(filepath: Path, expected_hash: Optional[str]) -> bool:
    """
    Validate checksum of a file.
    If expected_hash is None, generate and return True (will be recorded later).
    """
    if expected_hash is None:
        logger.info(f"No expected checksum provided for {filepath}, generating new one.")
        return True
    
    actual_hash = compute_sha256(filepath)
    if actual_hash == expected_hash:
        logger.info(f"Checksum verified for {filepath}")
        return True
    else:
        logger.error(f"Checksum mismatch for {filepath}. Expected: {expected_hash}, Got: {actual_hash}")
        return False

def filter_dataset_columns(filepath: Path, required_cols: List[str]) -> bool:
    """
    Check if a dataset (parquet file) contains required columns.
    Returns True if valid, False otherwise.
    """
    try:
        # Load just the schema to check columns
        df = pd.read_parquet(filepath)
        cols = set(df.columns)
        missing = [c for c in required_cols if c not in cols]
        
        if missing:
            logger.warning(f"Dataset {filepath} missing required columns: {missing}")
            return False
        
        logger.info(f"Dataset {filepath} has all required columns: {required_cols}")
        return True
    except Exception as e:
        logger.error(f"Error checking columns in {filepath}: {e}")
        return False

def write_exclusion_log(dataset_id: str, source: str, reason: str, exclusion_log: List[Dict]) -> List[Dict]:
    """Add an entry to the exclusion log."""
    exclusion_log.append({
        'dataset_id': dataset_id,
        'source': source,
        'reason': reason,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    })
    return exclusion_log

def write_blocked_status(reason: str) -> None:
    """Write the blocked status file."""
    status = {
        "status": "blocked",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(BLOCKED_STATUS_PATH, 'w') as f:
        json.dump(status, f, indent=2)
    logger.error(f"BLOCKED: {reason}")

def update_readme_status(dataset_id: str, source: str, status: str, reason: Optional[str] = None) -> None:
    """
    Update the README.md with the status of a dataset.
    Note: This function is called by T013, but we define it here for completeness.
    T012 writes to exclusion_log, T013 reads exclusion_log and updates README.
    """
    pass 

def run_download_pipeline() -> int:
    """
    Main pipeline logic for T012.
    1. Read IDs from dataset_ids.txt.
    2. Fetch datasets.
    3. Compute/Verify checksums.
    4. Filter for required columns.
    5. Log exclusions.
    6. If 0 valid, write blocked_status.json and exit.
    """
    REQUIRED_COLS = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Read IDs
    datasets = parse_dataset_ids(DATASET_IDS_PATH)
    if not datasets:
        write_blocked_status("No dataset IDs found in data/dataset_ids.txt")
        return 1
    
    logger.info(f"Found {len(datasets)} dataset IDs to process.")
    
    valid_datasets = []
    exclusion_log = []
    
    # Load existing exclusion log if present
    if EXCLUSION_LOG_PATH.exists():
        try:
            with open(EXCLUSION_LOG_PATH, 'r') as f:
                exclusion_log = json.load(f)
        except json.JSONDecodeError:
            exclusion_log = []

    for ds_info in datasets:
        ds_id = ds_info['id']
        source = ds_info['source']
        logger.info(f"Processing dataset: {ds_id} ({source})")
        
        # 2. Fetch dataset
        if source == 'openml':
            filepath = fetch_openml_dataset(ds_id)
        elif source == 'huggingface':
            filepath = fetch_huggingface_dataset(ds_id)
        else:
            reason = f"Unknown source: {source}"
            exclusion_log = write_exclusion_log(ds_id, source, reason, exclusion_log)
            continue
        
        if filepath is None:
            reason = "Failed to download dataset"
            exclusion_log = write_exclusion_log(ds_id, source, reason, exclusion_log)
            continue
        
        # 3. Checksum (Simplified: generate if missing, verify if present in README)
        # Since T012c handles README updates, we assume no expected hash here for now
        # or we could parse README to find it. For T012, we generate and log.
        # Implementation note: T012c is the one that updates README with checksums.
        # So here we just ensure the file is valid.
        
        # 4. Filter columns
        if not filter_dataset_columns(filepath, REQUIRED_COLS):
            reason = f"Missing required columns: {REQUIRED_COLS}"
            exclusion_log = write_exclusion_log(ds_id, source, reason, exclusion_log)
            continue
        
        # Valid
        valid_datasets.append({
            'id': ds_id,
            'source': source,
            'path': str(filepath),
            'checksum': compute_sha256(filepath)
        })
        logger.info(f"Dataset {ds_id} is valid.")
    
    # 5. Write exclusion log
    with open(EXCLUSION_LOG_PATH, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log written to {EXCLUSION_LOG_PATH}")
    
    # 6. CRITICAL BLOCKER
    if len(valid_datasets) == 0:
        write_blocked_status(
            f"No valid datasets found after download and filtering. "
            f"The provided dataset IDs ({', '.join([d['id'] for d in datasets])}) "
            f"do not exist or do not contain the required columns."
        )
        return 1
    
    logger.info(f"Pipeline completed successfully. {len(valid_datasets)} valid datasets found.")
    return 0

def main():
    logger.info("Starting T012: Data Download & Validation")
    exit_code = run_download_pipeline()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
