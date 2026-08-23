"""
T002d: Compute and record the SHA-256 checksum of the downloaded full ERA5 file.

This script computes the SHA-256 checksum of `data/raw/era5_full.h5` and updates
the project state file `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`
under the key `artifact_hashes.era5_full`. It also updates the `updated_at` timestamp
to comply with Constitution Principle V.
"""
import hashlib
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
import yaml

# Configure logging to output to console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/logs/data_validation_log.txt')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ERA5_FULL_PATH = PROJECT_ROOT / "data" / "raw" / "era5_full.h5"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    logger.info(f"Computing SHA-256 checksum for: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum: {e}")
        raise

def update_state_file(checksum: str) -> None:
    """Update the state YAML file with the new checksum and timestamp."""
    logger.info(f"Updating state file: {STATE_FILE_PATH}")
    
    if not STATE_FILE_PATH.exists():
        # If the state file doesn't exist, create it with the initial structure
        logger.warning(f"State file not found. Creating new file: {STATE_FILE_PATH}")
        state_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {
                "era5_full": checksum
            }
        }
    else:
        # Load existing state
        try:
            with open(STATE_FILE_PATH, "r") as f:
                state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise

        # Ensure required keys exist
        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}
        
        # Update the checksum
        state_data["artifact_hashes"]["era5_full"] = checksum
        
        # Update the timestamp
        state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Write back to file
    try:
        # Ensure parent directory exists
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(STATE_FILE_PATH, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Successfully updated state file with checksum: {checksum}")
    except Exception as e:
        logger.error(f"Error writing state file: {e}")
        raise

def main():
    """Main entry point for T002d."""
    logger.info("Starting T002d: Checksum ERA5 Full Dataset")
    
    try:
        # Verify file exists
        if not ERA5_FULL_PATH.exists():
            raise FileNotFoundError(
                f"Required ERA5 full dataset not found at {ERA5_FULL_PATH}. "
                "Please ensure T002c (Execute Fetch) has completed successfully."
            )
        
        # Compute checksum
        checksum = compute_sha256(ERA5_FULL_PATH)
        logger.info(f"Checksum computed: {checksum}")
        
        # Update state file
        update_state_file(checksum)
        
        # Log success to validation log
        logger.info(f"T002d COMPLETED: Checksum recorded for era5_full.h5")
        
        return 0
        
    except Exception as e:
        logger.error(f"T002d FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
