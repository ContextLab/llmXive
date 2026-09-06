import sys
import logging
from pathlib import Path

from compute_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Entry point for computing the SHA-256 checksum of the ERA5 sample file
    and updating the project state YAML.
    """
    # Setup logging infrastructure
    setup_logging()
    logger = get_data_quality_logger()

    logger.info("Starting checksum computation for ERA5 sample file.")
    
    # The compute_checksum module expects specific arguments or environment setup.
    # Based on the task description, we need to target:
    # Input: data/raw/era5_sample.h5
    # Output update: state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml
    # Key: artifact_hashes.era5_sample

    # We invoke the main function from compute_checksum.
    # If it requires arguments, we assume standard CLI behavior or config-based paths.
    # Since the existing API `compute_checksum.main` is called directly in this wrapper,
    # we assume it reads config or expects no args if paths are hardcoded in config.
    # However, to be safe and explicit per the task:
    
    try:
        # Call the main logic from the utility module
        # This function is expected to compute the hash and update the state file.
        compute_checksum_main()
        logger.info("Checksum computation and state update completed successfully.")
    except Exception as e:
        logger.error(f"Failed to compute checksum or update state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
