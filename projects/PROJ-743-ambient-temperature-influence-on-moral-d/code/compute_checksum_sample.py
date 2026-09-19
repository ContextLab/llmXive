"""
Task T003: Compute SHA-256 checksum of data/raw/era5_sample.h5 and update state file.
"""
import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Import shared utilities from the existing API surface
from compute_checksum import compute_sha256, ensure_state_file_exists, update_state_file
from setup_logging import setup_logging, get_data_quality_logger

def main():
    # Setup logging
    logger = setup_logging()
    data_quality_logger = get_data_quality_logger()

    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    sample_path = project_root / "data" / "raw" / "era5_sample.h5"
    state_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

    # Ensure directories exist
    ensure_state_file_exists(state_path)

    if not sample_path.exists():
        msg = f"Error: Sample file not found at {sample_path}. T001b (validate_era5.py) must run first."
        logger.error(msg)
        data_quality_logger.error(msg)
        sys.exit(1)

    # Compute SHA-256
    checksum = compute_sha256(sample_path)
    logger.info(f"Computed SHA-256 for {sample_path}: {checksum}")
    data_quality_logger.info(f"Checksum computed: {checksum}")

    # Update state file
    # Key: artifact_hashes.era5_sample
    # Update updated_at timestamp
    update_state_file(
        state_path=state_path,
        artifact_key="artifact_hashes.era5_sample",
        value=checksum,
        timestamp_key="updated_at"
    )
    logger.info(f"Updated state file at {state_path} with checksum for era5_sample.")
    data_quality_logger.info("State file updated successfully.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
