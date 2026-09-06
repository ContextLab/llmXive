import os
import sys
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ensure we can import from the code directory if running as script
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from update_state_checksum import compute_sha256, update_state_file
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Compute SHA-256 checksum of data/raw/era5_full.parquet and record it
    in state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
    under artifact_hashes.era5_full, updating updated_at.
    """
    logger = setup_logging()
    logger.info("Starting checksum computation for ERA5 full dataset.")

    # Define paths
    project_root = Path(__file__).parent.parent
    data_file_path = project_root / "data" / "raw" / "era5_full.parquet"
    state_file_path = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"

    # Verify data file exists
    if not data_file_path.exists():
        logger.error(f"Data file not found: {data_file_path}")
        logger.error("T002d (stream_era5.py) must complete successfully to generate this file.")
        sys.exit(1)

    if data_file_path.stat().st_size == 0:
        logger.error(f"Data file is empty: {data_file_path}")
        sys.exit(1)

    # Compute checksum
    checksum = compute_sha256(data_file_path)
    logger.info(f"Computed SHA-256 checksum: {checksum}")

    # Update state file
    if not state_file_path.exists():
        logger.error(f"State file not found: {state_file_path}")
        sys.exit(1)

    updated = update_state_file(
        state_file_path=state_file_path,
        artifact_key="era5_full",
        checksum=checksum
    )

    if updated:
        logger.info(f"Successfully updated state file: {state_file_path}")
        logger.info(f"Recorded checksum for era5_full: {checksum}")
    else:
        logger.error("Failed to update state file.")
        sys.exit(1)

    logger.info("Task T002e completed successfully.")

if __name__ == "__main__":
    main()
