"""
Task T037a: Run hash_artifacts.py to update state/ with hashes after T015 (Data Download).

This script executes the hashing pipeline to generate SHA-256 checksums for all
artifacts in the data/raw/ and code/ directories, ensuring reproducibility and
integrity of the dataset downloaded in T015.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import main as hash_main, hash_artifacts
from utils.logging import setup_logging, get_logger
from config import get_config

def main():
    """
    Main entry point for T037a.
    Executes the artifact hashing process and saves the state.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting T037a: Hashing artifacts after Data Download (T015)")

    try:
        config = get_config()
        # Ensure state directory exists
        state_dir = config.state_dir
        state_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"State directory ensured: {state_dir}")

        # Define paths to hash based on project structure
        # We hash the code/ directory (source) and data/raw/ (downloaded data)
        # as per the task description "update state/ with hashes after T015"
        paths_to_hash = [
            config.code_dir,
            config.data_raw_dir
        ]

        logger.info(f"Hashing paths: {paths_to_hash}")

        # Execute the hash artifacts logic
        # The hash_artifacts function in utils/hash_artifacts.py handles the scanning
        # and saving to state/
        results = hash_artifacts(
            paths=paths_to_hash,
            output_dir=state_dir,
            logger=logger
        )

        if results:
            logger.info(f"Successfully hashed {len(results)} files.")
            logger.info(f"Hash manifest saved to: {state_dir / 'artifact_hashes.json'}")
        else:
            logger.warning("No artifacts were hashed. Check if directories are empty or missing.")
            # Do not fail if directories are empty, just log warning
            # (T015 might have created structure but no files yet, though unlikely)

        logger.info("T037a completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Failed to complete T037a: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())