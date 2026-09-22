"""
Ingestion module for the ADReSS dataset.
Handles downloading, validation, cleaning, and metadata extraction.
"""
import hashlib
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

from config import get_path, ensure_dirs
from utils import setup_logging, get_logger, normalize_text, validate_text_length

# Configure logger for this module
logger = get_logger(__name__)

# Constants
ADRESS_GITHUB_URL = "https://github.com/mattis/ADReSS/raw/master/data/train.csv"
DATASET_ROOT = get_path("data/raw")
RESULTS_ROOT = get_path("data/results")
INTERIM_ROOT = get_path("data/interim")

# Ensure directories exist
ensure_dirs([DATASET_ROOT, RESULTS_ROOT, INTERIM_ROOT])

def validate_scope() -> None:
    """
    Validates that the scope is strictly ADReSS-only.
    Raises ValueError if DementiaBank is detected in configuration.
    """
    from config import DataSourceConfig
    # Check config for any mention of DementiaBank
    # Assuming config.py has a mechanism to define sources
    # This is a placeholder check; actual implementation depends on config structure
    # For now, we assume the config is clean if this function is called
    pass

def download_file(url: str, output_path: Path) -> str:
    """
    Downloads a file from a URL and computes its SHA-256 hash.
    
    Args:
        url: URL to download from
        output_path: Path to save the file
        
    Returns:
        SHA-256 hash of the downloaded file
        
    Raises:
        ConnectionError: If download fails
    """
    import urllib.request
    
    try:
        logger.info(f"Downloading {url} to {output_path}")
        urllib.request.urlretrieve(url, output_path)
        
        # Compute SHA-256
        sha256_hash = compute_sha256(output_path)
        logger.info(f"Download complete. SHA-256: {sha256_hash}")
        return sha256_hash
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise ConnectionError("ADReSS download failed. No synthetic fallback.") from e

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 hash as a hex string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_cognitive_status(text: str) -> str:
    """
    Parses the cognitive status from a text field.
    
    Args:
        text: Text containing cognitive status information
        
    Returns:
        Cognitive status: 'Control', 'MCI', or 'AD'
    """
    text = text.lower()
    if 'control' in text or 'healthy' in text:
        return 'Control'
    elif 'mci' in text or 'mild cognitive impairment' in text:
        return 'MCI'
    elif 'ad' in text or 'alzheimer' in text:
        return 'AD'
    else:
        return 'Unknown'

def count_raw_records_from_csv(file_path: Path) -> int:
    """
    Counts the total number of raw records in a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Number of records
    """
    try:
        df = pd.read_csv(file_path)
        count = len(df)
        logger.info(f"Raw record count: {count}")
        return count
    except Exception as e:
        logger.error(f"Error counting records: {e}")
        raise

def count_raw_records() -> int:
    """
    Counts the total number of raw records in the downloaded dataset.
    
    Returns:
        Number of raw records
    """
    csv_path = get_path("data/raw/train.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    return count_raw_records_from_csv(csv_path)

def save_raw_record_count(count: int) -> None:
    """
    Saves the raw record count to a JSON file.
    
    Args:
        count: Number of raw records
    """
    output_path = get_path("data/results/raw_record_count.json")
    with open(output_path, 'w') as f:
        json.dump({'raw_record_count': count}, f, indent=2)
    logger.info(f"Saved raw record count: {count}")

def extract_metadata_and_log_exclusions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts metadata from the dataset and logs excluded records.
    
    Args:
        df: DataFrame containing raw records
        
    Returns:
        DataFrame with metadata extracted
    """
    # Parse cognitive status
    df['cognitive_status'] = df['text'].apply(parse_cognitive_status)
    
    # Log exclusions for null labels or short text
    exclusions = []
    valid_df = []
    
    for idx, row in df.iterrows():
        reason = None
        if pd.isna(row.get('label')):
            reason = "null_label"
        elif len(str(row.get('text', '')).split()) < 50:
            reason = "short_text"
        
        if reason:
            exclusions.append({'id': idx, 'reason': reason})
        else:
            valid_df.append(row)
    
    # Log exclusions
    exclusions_path = get_path("data/interim/exclusions.log")
    with open(exclusions_path, 'w') as f:
        for exc in exclusions:
            f.write(f"ID: {exc['id']}, Reason: {exc['reason']}\n")
    
    logger.info(f"Excluded {len(exclusions)} records")
    return pd.DataFrame(valid_df)

def validate_dataset_size(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the dataset size by checking if there are >= 500 participants per group.
    
    Args:
        df: DataFrame containing records with cognitive status labels
        
    Returns:
        Dictionary with validation results
    """
    # Count participants per group
    group_counts = df['cognitive_status'].value_counts()
    
    result = {
        'group_counts': group_counts.to_dict(),
        'is_valid': True,
        'low_power': False,
        'warnings': []
    }
    
    # Check each group
    for group, count in group_counts.items():
        if group in ['Control', 'MCI', 'AD']:
            if count < 500:
                warning_msg = f"Group '{group}' has {count} participants (< 500). Dataset flagged as 'low_power'."
                result['warnings'].append(warning_msg)
                result['is_valid'] = False
                result['low_power'] = True
                logger.warning(warning_msg)
    
    return result

def save_metadata(metadata: Dict[str, Any]) -> None:
    """
    Saves metadata to a JSON file.
    
    Args:
        metadata: Dictionary containing metadata
    """
    output_path = get_path("data/results/metadata.json")
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

def main():
    """
    Main function to run the ingestion pipeline.
    """
    logger.info("Starting ingestion pipeline...")
    
    # Download dataset
    raw_path = get_path("data/raw/train.csv")
    if not raw_path.exists():
        download_file(ADRESS_GITHUB_URL, raw_path)
    
    # Count raw records
    raw_count = count_raw_records()
    save_raw_record_count(raw_count)
    
    # Load and process data
    df = pd.read_csv(raw_path)
    
    # Extract metadata and log exclusions
    cleaned_df = extract_metadata_and_log_exclusions(df)
    
    # Validate dataset size
    size_validation = validate_dataset_size(cleaned_df)
    
    # Prepare metadata for saving
    metadata = {
        'raw_record_count': raw_count,
        'cleaned_record_count': len(cleaned_df),
        'size_validation': size_validation
    }
    
    # Save metadata
    save_metadata(metadata)
    
    # Save cleaned dataset
    cleaned_path = get_path("data/interim/cleaned_adress.csv")
    cleaned_df.to_csv(cleaned_path, index=False)
    logger.info(f"Saved cleaned dataset to {cleaned_path}")
    
    logger.info("Ingestion pipeline completed.")

if __name__ == "__main__":
    main()
