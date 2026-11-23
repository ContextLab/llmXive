import csv
import hashlib
import json
import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def load_csv(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_parquet(path: Union[str, Path]) -> 'pd.DataFrame':
    """Load a Parquet file into a pandas DataFrame."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required to load parquet files")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_parquet(path)

def compute_sha256(path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    path = Path(path)
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(path: Union[str, Path], expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_sha256(path)
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch for {path}: expected {expected_checksum}, got {actual_checksum}")
        return False
    return True

def write_checksum_to_state(checksums: Dict[str, str], state_file: Union[str, Path]) -> None:
    """Write successful checksums to the state file."""
    state_file = Path(state_file)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    existing_checksums = {}
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                existing_checksums = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_checksums = {}
    
    existing_checksums.update(checksums)
    
    with open(state_file, 'w') as f:
        json.dump(existing_checksums, f, indent=2)
    logger.info(f"Checksums written to {state_file}")

def hash_artifact(path: Union[str, Path]) -> str:
    """Generate a hash for an artifact."""
    return compute_sha256(path)

def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Write data to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Data written to {path}")
