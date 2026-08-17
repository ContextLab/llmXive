import hashlib
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml
from typing import Optional, Dict, Any

from config import get_path_env_override
from utils import compute_sha256, update_state_file_with_checksums

logger = logging.getLogger(__name__)

def ensure_state_file_exists(state_path: Path) -> None:
    """Ensure the state YAML file exists and has the required structure."""
    if not state_path.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "artifact_hashes": {},
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(state_path, 'w') as f:
            yaml.dump(initial_data, f)
        logger.info(f"Created new state file: {state_path}")
    else:
        logger.info(f"State file exists: {state_path}")

def update_state_file(state_path: Path, key: str, value: str) -> None:
    """Update the state file with a new checksum and timestamp."""
    try:
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        if "artifact_hashes" not in data:
            data["artifact_hashes"] = {}
        
        data["artifact_hashes"][key] = value
        data["updated_at"] = datetime.utcnow().isoformat()
        
        with open(state_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        
        logger.info(f"Updated state file: {key} = {value}")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        raise

def main():
    """
    Main entry point for computing the checksum of the ERA5 sample file.
    This function is designed to be called by run_compute_checksum_sample.py.
    It targets `data/raw/era5_sample.h5` and updates the state file.
    """
    # Define paths
    project_root = Path(".")
    sample_file_path = project_root / "data" / "raw" / "era5_sample.h5"
    state_file_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    
    # Ensure state file exists
    ensure_state_file_exists(state_file_path)
    
    # Check if sample file exists
    if not sample_file_path.exists():
        logger.error(f"Sample file not found: {sample_file_path}")
        sys.exit(1)
    
    # Compute checksum
    try:
        checksum = compute_sha256(sample_file_path)
        logger.info(f"Computed SHA-256 for {sample_file_path}: {checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        sys.exit(1)
    
    # Update state file
    try:
        update_state_file(state_file_path, "era5_sample", checksum)
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        sys.exit(1)
    
    logger.info("T003: Checksum computed and recorded successfully.")

if __name__ == "__main__":
    main()