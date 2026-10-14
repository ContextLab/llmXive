"""
General utility functions including checksums and state management.
"""
import hashlib
import logging
import yaml
from pathlib import Path
from datetime import datetime, timezone

log = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    Returns:
        The hexadecimal SHA-256 hash.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_state_file(state_file_path: Path, key: str, value: str):
    """
    Update a nested key in the project state YAML file.
    
    Args:
        state_file_path: Path to the YAML state file.
        key: Dot-separated path to the value (e.g., 'artifact_hashes.raw_data').
        value: The value to set.
    """
    if not state_file_path.exists():
        state = {}
    else:
        with open(state_file_path, "r") as f:
            state = yaml.safe_load(f) or {}

    keys = key.split('.')
    curr = state
    for k in keys[:-1]:
        curr = curr.setdefault(k, {})
    
    curr[keys[-1]] = value
    
    # Ensure directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file_path, "w") as f:
        yaml.dump(state, f)
