import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Import shared utilities from existing API surface
# compute_checksum.py exposes: ensure_state_file_exists, compute_sha256, update_state_file, main
from compute_checksum import ensure_state_file_exists, compute_sha256, update_state_file

# Setup basic logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    T003: Compute SHA-256 checksum of data/raw/era5_sample.h5
    and record it in state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
    under artifact_hashes.era5_sample, updating updated_at.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_file_path = project_root / "data" / "raw" / "era5_sample.h5"
    state_file_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

    # Ensure the state file exists (creates empty structure if missing)
    ensure_state_file_exists(state_file_path)

    # Check if the input data file exists
    if not data_file_path.exists():
        logger.error(f"Data file not found: {data_file_path}")
        sys.exit(1)

    logger.info(f"Computing checksum for: {data_file_path}")

    # Compute SHA-256 checksum
    checksum = compute_sha256(data_file_path)

    if not checksum:
        logger.error("Failed to compute checksum.")
        sys.exit(1)

    logger.info(f"Checksum computed: {checksum}")

    # Update the state file with the new checksum and timestamp
    # We pass the specific key 'artifact_hashes.era5_sample' to update_state_file
    # to ensure it updates the correct nested path.
    success = update_state_file(
        state_file_path,
        "artifact_hashes.era5_sample",
        checksum,
        "updated_at"
    )

    if success:
        logger.info(f"Successfully updated state file: {state_file_path}")
        logger.info(f"Recorded checksum for era5_sample: {checksum}")
    else:
        logger.error("Failed to update state file.")
        sys.exit(1)

if __name__ == "__main__":
    main()