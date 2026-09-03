"""
Utility module for computing checksums and updating the project state file.
Used by T003 (Sample) and T002d (Full).
"""
import hashlib
import os
import sys
import logging
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_NAME = "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

# Specific file paths for tasks
ERA5_SAMPLE_PATH = DATA_RAW_DIR / "era5_sample.h5"
ERA5_FULL_PATH = DATA_RAW_DIR / "era5_full.h5"

def ensure_state_file_exists():
    """Ensures the state YAML file exists, creating an empty one if necessary."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE_PATH.exists():
        STATE_FILE_PATH.write_text(yaml.dump({"artifact_hashes": {}, "updated_at": None}))
        logging.info(f"Created new state file at {STATE_FILE_PATH}")

def compute_sha256(file_path: Path) -> str:
    """Computes the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(checksum_key: str, checksum_value: str):
    """
    Updates the state YAML file with a new checksum and current timestamp.
    """
    ensure_state_file_exists()
    
    with open(STATE_FILE_PATH, "r") as f:
        try:
            state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logging.error(f"Failed to parse state file: {e}")
            raise

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    state_data["artifact_hashes"][checksum_key] = checksum_value
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(STATE_FILE_PATH, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Updated state file: {checksum_key} = {checksum_value}")

def main():
    """
    Main entry point for T003 (Sample) and T002d (Full) logic.
    Determines which file to checksum based on the existence of the sample file.
    If both exist, this script is designed to be called specifically for the sample
    via the runner, but we implement a fallback check here for robustness.
    
    For T003 specifically, we target ERA5_SAMPLE_PATH.
    """
    logger = logging.getLogger(__name__)
    
    # Determine target file based on the task context.
    # T003 specifically targets the sample file.
    target_file = ERA5_SAMPLE_PATH
    checksum_key = "era5_sample"
    
    if not target_file.exists():
        logger.error(f"Target file not found: {target_file}")
        logger.error("T003 cannot proceed: data/raw/era5_sample.h5 is missing.")
        # Do not return 0 if the file is missing; this is a failure condition.
        return 1

    try:
        checksum = compute_sha256(target_file)
        logger.info(f"Computed SHA-256 for {target_file.name}: {checksum}")
        
        update_state_file(checksum_key, checksum)
        
        logger.info(f"T003 SUCCESS: Checksum for {checksum_key} recorded in state.")
        return 0
    except Exception as e:
        logger.error(f"Error computing checksum or updating state: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
