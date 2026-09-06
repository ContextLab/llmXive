"""
Update State File Task (T037)

Calculates MD5 checksums for raw data artifacts and updates the project state file.
This script is designed to be run manually after data acquisition tasks (T012, T013)
have successfully generated the CSV files.
"""

import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path if running from subdirectory
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

# Configure paths relative to project root
PROJECT_ID = "PROJ-487-the-impact-of-social-media-doomscrolling"
RAW_DATA_DIR = project_root / "data" / "raw"
STATE_DIR = project_root / "state" / "projects"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

# Artifacts to checksum
ARTIFACTS = {
    "gdelt_events": "gdelt_events.csv",
    "google_trends": "google_trends.csv"
}

logger = get_logger(__name__)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or return a default structure if missing."""
    import yaml

    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Creating new structure.")
        return {
            "project_id": PROJECT_ID,
            "last_updated": None,
            "artifact_hashes": {}
        }

    with open(state_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save state dictionary to YAML file."""
    import yaml
    from datetime import datetime

    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp
    state["last_updated"] = datetime.now().isoformat()

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_hashes(state: Dict[str, Any]) -> Dict[str, str]:
    """Calculate hashes for defined artifacts and update state."""
    import yaml

    new_hashes = {}

    for key, filename in ARTIFACTS.items():
        file_path = RAW_DATA_DIR / filename

        if not file_path.exists():
            logger.error(f"Required artifact missing: {file_path}")
            logger.error(f"Please ensure T012 and T013 have completed successfully.")
            raise FileNotFoundError(f"Missing artifact: {filename}")

        try:
            checksum = calculate_md5(file_path)
            new_hashes[key] = checksum
            logger.info(f"Calculated MD5 for {filename}: {checksum}")
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {filename}: {e}")
            raise

    state["artifact_hashes"] = new_hashes
    return new_hashes

def main():
    """Main entry point for T037."""
    logger.info("Starting T037: Update State File")
    logger.info(f"Project ID: {PROJECT_ID}")
    logger.info(f"Raw Data Directory: {RAW_DATA_DIR}")
    logger.info(f"State File Target: {STATE_FILE}")

    # Pre-check: Verify raw data files exist before attempting update
    missing_files = []
    for key, filename in ARTIFACTS.items():
        if not (RAW_DATA_DIR / filename).exists():
            missing_files.append(filename)

    if missing_files:
        logger.error(f"Aborting: Missing required raw data files: {missing_files}")
        logger.error("Ensure T012 (GDELT fetch) and T013 (Google Trends fetch) have completed.")
        sys.exit(1)

    try:
        # Load current state
        state = load_state(STATE_FILE)

        # Update hashes
        new_hashes = update_artifact_hashes(state)

        # Save updated state
        save_state(STATE_FILE, state)

        logger.info("State file updated successfully.")
        logger.info(f"New artifact hashes: {new_hashes}")

        # Verify the file was written
        if STATE_FILE.exists():
            logger.info(f"Verification: State file exists at {STATE_FILE}")
        else:
            logger.error("Verification failed: State file was not written.")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"File Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during state update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()