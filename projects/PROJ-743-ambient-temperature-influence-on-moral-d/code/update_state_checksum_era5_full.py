"""
Task T002d: Checksum ERA5
Compute and record the SHA-256 checksum of the downloaded full ERA5 file
(data/raw/era5_full.h5) in state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
under the key artifact_hashes.era5_full.
Crucially, this task MUST also update the updated_at timestamp in the same YAML file
to comply with Constitution Principle V.
"""
import hashlib
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
import yaml

# Project constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ERA5_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "era5_full.h5"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

def ensure_directories():
    """Ensure the state directory exists."""
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file, reading in chunks."""
    sha256_hash = hashlib.sha256()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def update_state_file(checksum: str):
    """
    Update the state YAML file with the new checksum and the current timestamp.
    Creates the file with default structure if it does not exist.
    """
    ensure_directories()
    
    current_time = datetime.now(timezone.utc).isoformat()
    
    # Load existing state or initialize new structure
    if STATE_FILE_PATH.exists():
        with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logging.error(f"Failed to parse existing state file: {e}")
                raise
    else:
        state_data = {}
    
    # Ensure required keys exist
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    # Update checksum and timestamp
    state_data["artifact_hashes"]["era5_full"] = checksum
    state_data["updated_at"] = current_time
    
    # Write back to file
    with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logging.info(f"Updated state file: {STATE_FILE_PATH}")
    logging.info(f"  - artifact_hashes.era5_full: {checksum}")
    logging.info(f"  - updated_at: {current_time}")

def main():
    """Main entry point for the checksum task."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting checksum computation for: {ERA5_FILE_PATH}")
    
    if not ERA5_FILE_PATH.exists():
        logger.error(f"Required file not found: {ERA5_FILE_PATH}")
        logger.error("Please ensure T002c (Execute Fetch) has completed successfully.")
        sys.exit(1)
    
    try:
        checksum = compute_sha256(ERA5_FILE_PATH)
        logger.info(f"Computed SHA-256: {checksum}")
        
        update_state_file(checksum)
        
        logger.info("Task T002d completed successfully.")
        
    except Exception as e:
        logger.error(f"An error occurred during checksum processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
