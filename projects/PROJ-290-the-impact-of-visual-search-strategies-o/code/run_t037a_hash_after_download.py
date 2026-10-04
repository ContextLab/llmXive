"""
Task T037a: Run hash_artifacts.py to update state/ with hashes after T015 (Data Download).

This script executes the artifact hashing pipeline specifically for the data/raw
directory and updates the state/ directory with the resulting checksums.
It ensures that the data downloaded and validated in T015 is cryptographically
recorded before proceeding to feature extraction.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the path to allow relative imports if necessary
# though the task implies running as a script from the root or via module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.hash_artifacts import main as hash_main, hash_artifacts
from utils.logging import setup_logging, get_logger
from config import get_config

def main():
    """
    Executes the hashing process for the data/raw directory and updates state/.
    """
    # Setup logging
    logger = setup_logging(log_level=logging.INFO)
    logger.info("Starting Task T037a: Hashing artifacts after Data Download (T015)")

    try:
        config = get_config()
        
        # Define paths based on config
        data_raw_dir = config.DATA_RAW_DIR
        state_dir = config.STATE_DIR
        
        logger.info(f"Scanning directory: {data_raw_dir}")
        logger.info(f"Output state directory: {state_dir}")

        if not os.path.exists(data_raw_dir):
            logger.error(f"Data raw directory does not exist: {data_raw_dir}. "
                         "Ensure T015 (Data Download) has been completed successfully.")
            sys.exit(1)

        if not os.path.exists(state_dir):
            logger.info(f"Creating state directory: {state_dir}")
            os.makedirs(state_dir, exist_ok=True)

        # Run the hash_artifacts logic
        # The hash_artifacts function from utils.hash_artifacts typically handles
        # scanning a directory and saving the manifest to state/
        # We invoke it targeting the data/raw directory.
        
        # Check the signature of hash_artifacts from the API surface:
        # hash_artifacts(scan_directory, output_state_dir) -> Dict
        # Note: The API surface says `hash_artifacts` is in `utils.hash_artifacts`.
        # We assume it takes a directory path and an output path or uses config.
        # Based on typical implementation patterns in this pipeline:
        
        result = hash_artifacts(data_raw_dir, state_dir)
        
        if result and 'status' in result and result['status'] == 'success':
            logger.info("Hashing completed successfully.")
            logger.info(f"Hash manifest saved to {os.path.join(state_dir, 'hash_manifest.json')}")
            logger.info(f"Files hashed: {result.get('files_count', 0)}")
            logger.info(f"Total size: {result.get('total_size_bytes', 0)} bytes")
        else:
            logger.warning("Hashing completed but returned unexpected status.")
            logger.debug(f"Result details: {result}")

    except Exception as e:
        logger.error(f"Error during hashing process: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Task T037a completed.")

if __name__ == "__main__":
    main()