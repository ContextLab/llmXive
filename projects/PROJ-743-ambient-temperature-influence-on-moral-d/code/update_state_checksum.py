"""
Generic Checksum Utility for Project State.

Provides functions to compute SHA-256 checksums and update the project state
YAML file with specific artifact hashes.
"""
import hashlib
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

def compute_sha256(file_path: str) -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Absolute or relative path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "rb") as f:
        # Read in chunks to handle large files (like ERA5) efficiently
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()

def ensure_state_file_exists(state_path: str) -> Path:
    """
    Ensures the state YAML file exists. Creates it with an empty structure if not.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Path object for the state file.
    """
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not path.exists():
        logging.info(f"Creating new state file: {state_path}")
        initial_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "status": "active",
            "artifact_hashes": {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(initial_data, f, default_flow_style=False, sort_keys=False)
    else:
        logging.info(f"Loading existing state file: {state_path}")
        
    return path

def update_state_file(state_path: str, checksum_key: str, checksum_value: str) -> None:
    """
    Updates the project state YAML file with a new checksum and timestamp.
    
    Args:
        state_path: Path to the state YAML file.
        checksum_key: The key under which to store the checksum (e.g., 'artifact_hashes.era5_sample').
        checksum_value: The computed SHA-256 hash string.
    """
    path = Path(state_path)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            
        # Ensure artifact_hashes dictionary exists
        if "artifact_hashes" not in data:
            data["artifact_hashes"] = {}
            
        # Split key if dot-notation is used (e.g., "artifact_hashes.era5_sample")
        keys = checksum_key.split(".")
        current = data["artifact_hashes"]
        
        # Navigate to the parent key if nested (though current requirement is flat under artifact_hashes)
        # For T003, key is "artifact_hashes.era5_sample", so we need to ensure we are updating the correct spot.
        # The logic below assumes the first part of the key is the top-level dict if it matches the root structure.
        # However, the requirement says "record it under artifact_hashes.era5_sample".
        # Let's assume the data structure is: { "artifact_hashes": { "era5_sample": "..." } }
        
        if keys[0] == "artifact_hashes":
            target_key = keys[1] if len(keys) > 1 else keys[0]
            data["artifact_hashes"][target_key] = checksum_value
        else:
            # Fallback if key doesn't start with artifact_hashes
            data[checksum_key] = checksum_value
            
        # Update timestamp
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
        logging.info(f"Updated state file: {checksum_key} = {checksum_value[:16]}...")
        
    except Exception as e:
        logging.error(f"Failed to update state file {state_path}: {e}")
        raise

def main(file_path: str, state_path: str, checksum_key: str) -> None:
    """
    Main entry point for the checksum utility script.
    
    Args:
        file_path: Path to the file to checksum.
        state_path: Path to the state YAML file to update.
        checksum_key: The key in the YAML file to store the checksum.
    """
    logger = logging.getLogger(__name__)
    
    # 1. Compute Checksum
    checksum = compute_sha256(file_path)
    logger.info(f"Computed SHA-256 for {file_path}: {checksum}")
    
    # 2. Ensure State File Exists
    ensure_state_file_exists(state_path)
    
    # 3. Update State File
    update_state_file(state_path, checksum_key, checksum)
    
    logger.info("Checksum process completed successfully.")

if __name__ == "__main__":
    # Default arguments for standalone execution if not passed via main()
    # This block is primarily for testing the module directly
    if len(sys.argv) < 4:
        print("Usage: python update_state_checksum.py <file_path> <state_path> <checksum_key>")
        sys.exit(1)
        
    main(sys.argv[1], sys.argv[2], sys.argv[3])
