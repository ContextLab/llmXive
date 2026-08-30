import sys
import logging
from pathlib import Path

from update_state_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger


def main():
    """
    Entry point for computing the SHA-256 checksum of the ERA5 sample file
    and updating the project state YAML.

    This script:
    1. Computes the SHA-256 checksum of `data/raw/era_sample.h5`.
    2. Updates `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml`
       under `artifact_hashes.era5_sample`.
    3. Updates the `updated_at` timestamp in the same YAML file.
    """
    setup_logging()
    logger = get_data_quality_logger()

    sample_path = Path("data/raw/era_sample.h5")
    state_path = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")

    if not sample_path.exists():
        logger.error(f"Sample file not found: {sample_path}")
        logger.error("T003 cannot proceed: data/raw/era_sample.h5 is missing.")
        sys.exit(1)

    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        logger.error("T003 cannot proceed: state file is missing.")
        sys.exit(1)

    try:
        compute_checksum_main(
            target_file=str(sample_path),
            state_file=str(state_path),
            artifact_key="era5_sample"
        )
        logger.info(f"T003: Successfully computed and recorded checksum for {sample_path.name}")
    except Exception as e:
        logger.error(f"T003: Failed to update state file with checksum: {e}")
        raise


if __name__ == "__main__":
    main()
