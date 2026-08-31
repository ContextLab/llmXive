import sys
import logging
from pathlib import Path

from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    T003: Compute SHA-256 checksum of data/raw/era5_sample.h5
    and record it under artifact_hashes.era5_sample in the state YAML.
    """
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T003: Checksum ERA5 Sample File")

    input_file = Path("data/raw/era5_sample.h5")
    state_file = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Required file {input_file} does not exist.")

    # Compute checksum and update state file
    # The imported main() from update_state_checksum handles the logic
    # It expects to be called with specific args or environment setup.
    # We will re-implement the specific logic here to ensure it targets the sample file.
    
    import hashlib
    import yaml
    from datetime import datetime, timezone

    sha256_hash = hashlib.sha256()
    with open(input_file, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()

    logger.info(f"Computed SHA-256 for {input_file}: {checksum}")

    if not state_file.exists():
        logger.error(f"State file not found: {state_file}")
        raise FileNotFoundError(f"State file {state_file} does not exist.")

    with open(state_file, "r") as f:
        state_data = yaml.safe_load(f)

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"]["era5_sample"] = checksum
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state file {state_file} with checksum for era5_sample")
    print(f"T003 Complete: Checksum {checksum} written to {state_file}")

if __name__ == "__main__":
    main()
