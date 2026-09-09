import hashlib
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
import yaml

def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_state_file_exists(state_file_path: Path):
    """Ensures the state YAML file exists."""
    if not state_file_path.exists():
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file_path, 'w') as f:
            yaml.dump({"artifact_hashes": {}, "updated_at": None}, f)

def update_state_file(state_file_path: Path, key: str, value: str):
    """Updates the state file with the new checksum and timestamp."""
    with open(state_file_path, 'r') as f:
        try:
            state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            state_data = {}

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"][key] = value
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(state_file_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Generic main for checksum tasks.
    This is a placeholder; specific tasks should define their own main logic
    or use the wrapper scripts (e.g., update_state_checksum_sample.py).
    """
    pass

if __name__ == "__main__":
    main()