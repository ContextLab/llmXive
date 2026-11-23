import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_dataset_metadata(output_path: str, data: Dict[str, Any]) -> None:
    """Write dataset metadata to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    logger.info(f"Metadata written to {output_path}")

def verify_metadata_hash(file_path: str, expected_hash: str) -> bool:
    """Verify the SHA256 hash of a file matches the expected hash."""
    if not os.path.exists(file_path):
        return False
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def load_csv_as_dict(file_path: str, key_col: str = None) -> Dict[str, Any]:
    """
    Load a CSV file and return it as a dictionary.
    If key_col is provided, use it as the dictionary key.
    Otherwise, return a list of dicts.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_csv(file_path)
    if key_col:
        if key_col not in df.columns:
            raise ValueError(f"Key column '{key_col}' not found in {file_path}")
        return df.set_index(key_col).to_dict(orient='index')
    return df.to_dict(orient='records')
