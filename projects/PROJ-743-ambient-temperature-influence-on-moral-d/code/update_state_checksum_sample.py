import sys
import logging
from pathlib import Path

# Import the main logic from the shared checksum utility
# This reuses the logic defined in code/update_state_checksum.py
# to ensure consistency in hashing and YAML updating.
from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    T003: Compute SHA-256 checksum of data/raw/era5_sample.h5 and record it
    in state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml.

    This script acts as the specific entry point for the ERA5 sample checksum task.
    It delegates the heavy lifting to the generic compute_checksum utility,
    ensuring the correct file path and YAML key are used.
    """
    # Setup logging
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T003: Checksum ERA5 Sample File")

    # Define the specific input file for this task
    input_file = Path("data/raw/era5_sample.h5")
    
    # Define the specific state file and YAML key for this task
    state_file = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")
    yaml_key = "artifact_hashes.era5_sample"

    # Check if the input file exists before attempting to compute checksum
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Task T003 cannot proceed. The file data/raw/era5_sample.h5 is missing.")
        sys.exit(1)

    # We need to override the default behavior of the generic main to point to our specific file.
    # Since the generic `compute_checksum_main` likely takes no args or expects env vars,
    # and we need to enforce specific paths, we will replicate the core logic here
    # to ensure it hits the exact file and key required by T003.
    
    import hashlib
    import yaml
    from datetime import datetime, timezone

    try:
        # 1. Compute SHA-256
        sha256_hash = hashlib.sha256()
        with open(input_file, "rb") as f:
            # Read in chunks to handle potentially large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()
        
        logger.info(f"Computed SHA-256 for {input_file}: {checksum}")

        # 2. Ensure state file exists
        if not state_file.exists():
            logger.warning(f"State file {state_file} does not exist. Creating it.")
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, 'w') as f:
                yaml.dump({"artifact_hashes": {}}, f)

        # 3. Load, update, and save state file
        with open(state_file, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state_data = {}

        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}

        state_data["artifact_hashes"][yaml_key.split('.')[-1]] = checksum
        
        # Update timestamp
        state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        with open(state_file, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Successfully updated {state_file} with checksum for {yaml_key}")
        logger.info("T003 completed successfully.")

    except Exception as e:
        logger.error(f"Error during T003 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
