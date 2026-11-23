"""
Task T008: Load the primary HEA dataset after it has been downloaded.

This module provides functionality to load the raw HEA dataset from disk.
It strictly distinguishes between 'file not found' (download failed) and
'file corrupted' (checksum mismatch) scenarios, logging the specific cause
and aborting with a clear error if the file is unavailable.

Depends on T140 (Download).
"""
import os
import logging
from pathlib import Path
from typing import Union, Optional
import pandas as pd
import hashlib
import json
import yaml

from utils.logging import get_logger
from utils.config import get_config

# Constants
RAW_DATA_PATH = "data/raw/heas_raw.csv"
STATE_FILE_PATH = "state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml"
SCHEMA_PATH = "contracts/dataset.schema.yaml"

logger = get_logger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> dict:
    """Load the project state file."""
    if not os.path.exists(STATE_FILE_PATH):
        logger.warning(f"State file not found: {STATE_FILE_PATH}")
        return {}
    try:
        with open(STATE_FILE_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {}

def load_raw_dataset(
    file_path: Optional[str] = None,
    validate_checksum: bool = True
) -> pd.DataFrame:
    """
    Load the primary HEA dataset from disk.
    
    CRITICAL: Distinguishes between 'file not found' and 'file corrupted' (checksum mismatch).
    
    Args:
        file_path: Path to the raw dataset. Defaults to RAW_DATA_PATH.
        validate_checksum: If True, compares file hash against the recorded state.
                           If False, skips checksum validation (only checks existence).
                           
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the raw dataset file does not exist.
        ValueError: If the file exists but the checksum does not match the recorded state.
    """
    if file_path is None:
        file_path = RAW_DATA_PATH
    
    file_path_obj = Path(file_path)
    
    # 1. Check if file exists
    if not file_path_obj.exists():
        logger.error(f"CRITICAL: Raw dataset file not found: {file_path}")
        logger.error("This indicates that the download step (T140) has not been executed successfully "
                     "or the file was deleted. The pipeline cannot proceed without the raw data.")
        raise FileNotFoundError(
            f"Raw dataset file not found: {file_path}. "
            "Please ensure the download step (T140) has been completed successfully."
        )
    
    logger.info(f"Found raw dataset at: {file_path}")
    
    # 2. Validate checksum if requested
    if validate_checksum:
        state = load_state()
        recorded_checksum = None
        
        # Navigate state structure for checksum
        # Expected structure: state.get('artifact_hashes', {}).get('data/raw/heas_raw.csv')
        artifact_hashes = state.get('artifact_hashes', {})
        recorded_checksum = artifact_hashes.get('data/raw/heas_raw.csv')
        
        if recorded_checksum:
            current_checksum = compute_sha256(file_path)
            
            if current_checksum != recorded_checksum:
                logger.error(f"CRITICAL: Checksum mismatch for {file_path}")
                logger.error(f"Recorded checksum: {recorded_checksum}")
                logger.error(f"Current checksum:  {current_checksum}")
                logger.error("This indicates the file has been modified or corrupted since the last valid run.")
                raise ValueError(
                    f"Checksum mismatch for {file_path}. "
                    f"Expected: {recorded_checksum}, Got: {current_checksum}. "
                    "The file may be corrupted or modified. Please re-run the download step."
                )
            else:
                logger.info(f"Checksum validation passed for {file_path}")
        else:
            logger.warning(f"No recorded checksum found in state file for {file_path}. "
                         "Skipping checksum validation. "
                         "Ensure T060 has run to record the checksum.")
    
    # 3. Load the data
    try:
        logger.info(f"Loading CSV from {file_path}...")
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to parse CSV file {file_path}: {e}")
        raise RuntimeError(f"Failed to load dataset: {e}") from e

def main():
    """
    Main entry point for T008.
    Attempts to load the dataset and prints status.
    """
    try:
        df = load_raw_dataset()
        print(f"SUCCESS: Loaded {len(df)} records from {RAW_DATA_PATH}")
        # Optional: print head for verification
        # print(df.head())
        return 0
    except FileNotFoundError as e:
        print(f"FAILURE: {e}")
        return 1
    except ValueError as e:
        print(f"FAILURE: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())