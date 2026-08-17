"""
Task T002d: Compute and record the SHA-256 checksum of the downloaded full ERA5 file.

This script:
1. Computes the SHA-256 checksum of `data/raw/era5_full.h5`.
2. Updates `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`
   with the new checksum under `artifact_hashes.era5_full`.
3. Updates the `updated_at` timestamp in the same YAML file to comply with
   Constitution Principle V.
"""
import hashlib
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("results/logs/data_validation_log.txt")
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ERA5_FULL_PATH = PROJECT_ROOT / "data" / "raw" / "era5_full.h5"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    logger.info(f"Computing SHA-256 for {file_path}...")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def update_state_file(state_path: Path, artifact_key: str, checksum: str):
    """Update the state YAML file with the new checksum and timestamp."""
    logger.info(f"Updating state file: {state_path}")
    
    if not state_path.exists():
        logger.warning(f"State file not found, creating new structure: {state_path}")
        state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {}
        }
    else:
        with open(state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        # Ensure required keys exist
        if "artifact_hashes" not in data:
            data["artifact_hashes"] = {}
    
    # Update the specific artifact checksum
    data["artifact_hashes"][artifact_key] = checksum
    
    # Update the timestamp (Constitution Principle V)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back to file
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Successfully updated {artifact_key} checksum and timestamp in {state_path}")

def main():
    """Main entry point for T002d."""
    try:
        # 1. Verify input file exists
        if not ERA5_FULL_PATH.exists():
            logger.error(f"Required input file missing: {ERA5_FULL_PATH}")
            logger.error("Task T002c (fetch full dataset) must be completed first.")
            sys.exit(1)

        # 2. Compute checksum
        checksum = compute_sha256(ERA5_FULL_PATH)
        logger.info(f"Checksum computed: {checksum}")

        # 3. Update state file
        update_state_file(STATE_FILE_PATH, "era5_full", checksum)

        logger.info("Task T002d completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Task T002d failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())