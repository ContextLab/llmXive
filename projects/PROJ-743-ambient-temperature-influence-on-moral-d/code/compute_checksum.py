import hashlib
import os
import sys
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path

def ensure_state_file_exists(state_file_path: Path):
    """Ensures the state YAML file exists, creating it with an empty structure if not."""
    if not state_file_path.exists():
        logging.warning(f"State file {state_file_path} does not exist. Creating it.")
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file_path, 'w') as f:
            yaml.dump({"artifact_hashes": {}, "updated_at": None}, f)

def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(state_file_path: Path, key: str, value: str):
    """Updates the state file with the new checksum and current timestamp."""
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
    Generic entry point for checksum computation.
    Expects environment variables or defaults for file paths.
    """
    # This function is kept for backward compatibility with other tasks
    # that might call it directly, but T003 uses a specific wrapper.
    pass

if __name__ == "__main__":
    main()
