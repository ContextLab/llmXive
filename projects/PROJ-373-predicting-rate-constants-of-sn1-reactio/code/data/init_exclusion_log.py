"""
Initialize the exclusion log file for the SN1 rate constant pipeline.

This script creates the `data/processed/exclusion_raw.log` CSV file with the
required headers: `row_index`, `reason`, `original_smiles`.

It ensures the file exists before downstream tasks (T011c, T012, T013) attempt
to append exclusion records.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger


def initialize_exclusion_log():
    """
    Create the exclusion log CSV file with headers if it does not exist.

    Returns:
        Path: The path to the created/existing exclusion log file.

    Raises:
        RuntimeError: If the file cannot be created or written to.
    """
    config = DataConfig()
    output_dir = Path(config.processed_dir)
    output_file = output_dir / "exclusion_raw.log"

    # Ensure the directory exists
    ensure_dirs()

    logger = get_logger("init_exclusion_log")

    # Check if file already exists
    if output_file.exists():
        logger.info(f"Exclusion log already exists at {output_file}. Skipping creation.")
        # Optional: Validate headers if it exists?
        # For now, we assume if it exists, it's valid or will be handled by upstream logic.
        return output_file

    try:
        # Create the file with headers
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            f.write("row_index,reason,original_smiles\n")

        logger.info(f"Successfully initialized exclusion log at {output_file}")
        return output_file

    except IOError as e:
        logger.error(f"Failed to create exclusion log at {output_file}: {e}")
        raise RuntimeError(f"Failed to initialize exclusion log: {e}")


def main():
    """
    Main entry point for the exclusion log initialization script.
    """
    logger = get_logger("init_exclusion_log")
    logger.info("Starting exclusion log initialization...")

    try:
        initialize_exclusion_log()
        logger.info("Exclusion log initialization completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Exclusion log initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
