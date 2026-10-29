"""
Wrapper script that orchestrates the full analysis pipeline with checksum
verification.  It is the entry point referenced in ``quickstart.md``.

The script performs the following steps:

1. Ensure the raw HEA dataset is present (delegates to ``data.download``).
2. Compute a SHA‑256 checksum of the raw dataset and compare it against the
   stored checksum in the state file.  Mismatches abort the run.
3. Run the data pipeline (pre‑processing, descriptor calculation, etc.).
4. Write a high‑level data‑status JSON file.

All artefacts are written under the project‑relative ``data`` and ``output``
directories, which are created on‑the‑fly by ``llmxive_toolkit.paths``.
"""

import argparse
import sys
import logging

from llmxive_toolkit import paths, get_logger
from data.download import download_dataset
from data.descriptors import main as descriptors_main
from data.status_writer import main as status_main
from data.checksum_raw import record_checksum, compute_sha256

logger = get_logger(__name__)

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the full HEA pipeline with checksum verification."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible steps (currently unused).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory where pipeline outputs will be stored.",
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)

    # Step 1: Ensure raw dataset exists (download if necessary)
    try:
        logger.info("Ensuring raw dataset is present...")
        download_dataset()  # uses default path data/raw/heas_raw.csv
    except FileNotFoundError as e:
        logger.error(f"Dataset not found and could not be downloaded: {e}")
        sys.exit(1)

    # Step 2: Verify checksum of the raw dataset
    raw_path = paths.data("raw", "heas_raw.csv")
    try:
        logger.info(f"Computing checksum for {raw_path}")
        checksum = compute_sha256(str(raw_path))
        recorded = record_checksum(str(raw_path))
        if checksum != recorded:
            logger.error(
                "Checksum mismatch for raw dataset. "
                f"Computed: {checksum}, Recorded: {recorded}"
            )
            sys.exit(1)
        logger.info("Checksum verification passed.")
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        sys.exit(1)

    # Step 3: Run descriptor generation (this also validates against schemas)
    try:
        logger.info("Running descriptor generation...")
        descriptors_main()
    except Exception as e:
        logger.error(f"Descriptor generation failed: {e}")
        sys.exit(1)

    # Step 4: Write data status JSON (row count, warnings, etc.)
    try:
        logger.info("Writing data status JSON...")
        status_main()
    except Exception as e:
        logger.error(f"Failed to write data status: {e}")
        sys.exit(1)

    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
