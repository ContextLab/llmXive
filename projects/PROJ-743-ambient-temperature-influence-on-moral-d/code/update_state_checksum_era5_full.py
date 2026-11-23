import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Ensure the path to config is available if needed, though we use relative paths here
# The project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
DATA_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "era5_full.parquet"

logger = logging.getLogger(__name__)

def ensure_state_file_exists():
    """Ensures the state YAML file exists, creating it with defaults if necessary."""
    if not STATE_FILE_PATH.exists():
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {}
        }
        with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(initial_data, f, default_flow_style=False)
        logger.info(f"Created new state file at {STATE_FILE_PATH}")

def compute_sha256(file_path):
    """Computes the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def update_state_file(checksum):
    """Updates the state YAML file with the new checksum and timestamp."""
    try:
        with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f)

        if state_data is None:
            state_data = {}

        if 'artifact_hashes' not in state_data:
            state_data['artifact_hashes'] = {}

        state_data['artifact_hashes']['era5_full'] = checksum
        state_data['updated_at'] = datetime.now(timezone.utc).isoformat()

        with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False)

        logger.info(f"Updated state file with checksum for era5_full: {checksum}")
    except Exception as e:
        logger.error(f"Error updating state file: {e}")
        raise

def main():
    """Main entry point for the task."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting checksum computation for ERA5 full dataset.")

    if not DATA_FILE_PATH.exists():
        logger.error(f"Data file not found: {DATA_FILE_PATH}. Aborting.")
        sys.exit(1)

    ensure_state_file_exists()

    try:
        checksum = compute_sha256(DATA_FILE_PATH)
        update_state_file(checksum)
        logger.info("Checksum computation and state update completed successfully.")
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()