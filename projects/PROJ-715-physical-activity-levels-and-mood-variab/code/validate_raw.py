import os
import sys
import logging
import hashlib
from pathlib import Path

import yaml

from config import get_path, init_logger

logger = init_logger(__name__)

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_hash() -> str:
    """Load the expected hash from the state file."""
    state_path = get_path('state', 'projects', 'PROJ-715-physical-activity-levels-and-mood-variab.yaml')
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found at {state_path}. Run ingest.py first.")
    
    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f)
    
    if not state_data or 'artifact_hashes' not in state_data:
        raise ValueError(f"State file at {state_path} is missing 'artifact_hashes'.")
    
    expected_hash = state_data['artifact_hashes'].get('data_raw_bronze')
    if not expected_hash:
        raise ValueError(f"State file missing 'data_raw_bronze' hash.")
    
    return expected_hash

def verify_bronze_integrity() -> bool:
    """
    Verify the integrity of data/raw/bronze.parquet against the recorded checksum.
    
    Raises:
        RuntimeError: If the file is missing or the checksum does not match.
    """
    parquet_path = get_path("data/raw", "bronze.parquet")
    
    if not parquet_path.exists():
        raise RuntimeError(f"Corrupted Data Check Failed: File missing at {parquet_path}. "
                           "Run code/ingest.py to download and convert the data.")
    
    if os.path.getsize(parquet_path) == 0:
        raise RuntimeError(f"Corrupted Data Check Failed: File at {parquet_path} is empty.")
    
    expected_hash = load_state_hash()
    actual_hash = compute_sha256(parquet_path)
    
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"Corrupted Data Check Failed: Checksum mismatch for {parquet_path}.\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}\n"
            "The data may be corrupted. Please re-run code/ingest.py."
        )
    
    logger.info(f"Integrity check passed for {parquet_path}.")
    return True

def main():
    """CLI entry point for raw data validation."""
    try:
        verify_bronze_integrity()
        logger.info("Validation successful.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()