import csv
import hashlib
import json
import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from utils.config import STATE, PROJECT_ID

logger = logging.getLogger(__name__)

def load_csv(file_path: str) -> List[Dict[str, Any]]:
    """Load a CSV file and return a list of dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def load_parquet(file_path: str) -> Any:
    """Load a Parquet file using pandas."""
    import pandas as pd
    return pd.read_parquet(file_path)

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual_checksum = compute_sha256(file_path)
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        return False
    logger.info(f"Checksum verified for {file_path}")
    return True

def write_checksum_to_state(file_path: str, checksum: str, project_id: str = PROJECT_ID):
    """
    Write successful checksum to state file.
    State file: state/projects/<project_id>.yaml
    """
    state_dir = STATE
    os.makedirs(state_dir, exist_ok=True)
    state_file = Path(state_dir) / f"{project_id}.yaml"

    data = {}
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

    if 'verified_checksums' not in data:
        data['verified_checksums'] = {}

    data['verified_checksums'][file_path] = {
        'checksum': checksum,
        'verified_at': str(os.path.getmtime(file_path)) # Using mtime as timestamp proxy
    }

    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    logger.info(f"Checksum written to state: {state_file}")

def hash_artifact(data: Any) -> str:
    """Hash arbitrary data (e.g., dict, list) to a string."""
    data_str = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(data_str).hexdigest()

def load_json(file_path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(data: Dict[str, Any], file_path: str):
    """Write a dictionary to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
