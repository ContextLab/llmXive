import sys
import logging
from pathlib import Path

# Import the core logic from the shared utils module
# The API surface indicates `update_state_checksum.py` has the main logic
from update_state_checksum import compute_sha256, ensure_state_file_exists, update_state_file
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    T003: Checksum ERA5 Sample File.
    
    Computes SHA-256 checksum of data/raw/era5_sample.h5 and records it
    under artifact_hashes.era5_sample in the project state YAML.
    """
    setup_logging()
    logger = get_data_quality_logger()
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    sample_file = project_root / "data" / "raw" / "era5_sample.h5"
    state_file = project_root / "state" / "projects" / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    
    # Verify the source file exists (T001b should have created it)
    if not sample_file.exists():
        logger.error(f"Source file not found: {sample_file}")
        logger.error("T001b (Validate ERA5 Sample) must be completed before T003.")
        sys.exit(1)
    
    logger.info(f"Computing checksum for: {sample_file}")
    
    # Compute SHA-256
    checksum = compute_sha256(sample_file)
    logger.info(f"Checksum computed: {checksum}")
    
    # Ensure state file exists and update it
    ensure_state_file_exists(state_file)
    
    # Update the specific key for the sample file
    update_state_file(
        state_file_path=state_file,
        key="artifact_hashes.era5_sample",
        value=checksum,
        logger=logger
    )
    
    logger.info("T003: Checksum recorded successfully.")
    print(f"Success: Checksum {checksum} recorded for era5_sample.h5")

if __name__ == "__main__":
    main()
