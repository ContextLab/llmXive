import hashlib
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(
    state_file_path: Path, 
    artifact_key: str, 
    checksum: str
) -> None:
    """
    Updates the state YAML file with the new checksum and timestamp.
    Handles missing keys and creates the file if it doesn't exist.
    """
    if not state_file_path.exists():
        logging.warning(f"State file {state_file_path} does not exist. Creating new one.")
        state_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "artifact_hashes": {},
            "updated_at": None
        }
    else:
        with open(state_file_path, "r") as f:
            state_data = yaml.safe_load(f) or {}
        
        # Ensure required keys exist
        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}
    
    # Update the specific artifact hash
    state_data["artifact_hashes"][artifact_key] = checksum
    
    # Update the timestamp to comply with Constitution Principle V
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Ensure directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write back to file
    with open(state_file_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Generic entry point. For specific tasks like T003, use the wrapper scripts
    that pass specific arguments or call update_state_file directly.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # This function is a placeholder if called directly without arguments.
    # The specific logic is handled by wrapper scripts like update_state_checksum_sample.py
    logger.info("update_state_checksum module loaded. Use specific wrapper for T003.")

if __name__ == "__main__":
    main()
