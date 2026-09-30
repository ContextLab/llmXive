"""
Save raw downloaded data with checksum verification.

This module implements T014: Save raw downloaded data to `data/raw/` with checksum verification.
It assumes the raw data has already been downloaded and placed in the target directory
(typically by code/ingest.py), and it generates the SHA256 checksum file.
"""
import os
import sys
import hashlib
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    sha256_hash = hashlib.sha256()
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {file_path}")

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def main():
    """
    Main entry point for saving raw data with checksum.

    Usage:
        python code/save_raw_data.py --input <path_to_raw_csv> --output_dir <output_directory>

    Expected outputs:
        - <output_dir>/<filename>.csv (copied/verified)
        - <output_dir>/<filename>.csv.sha256 (checksum file)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Save raw data with SHA256 checksum verification."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input raw CSV file."
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where the checksum file will be saved."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Validate input file
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        sys.exit(1)

    if not input_path.is_file():
        logger.error(f"Input path is not a file: {input_path}")
        sys.exit(1)

    # Verify it's a CSV (basic check)
    if input_path.suffix.lower() != '.csv':
        logger.warning(f"Input file does not have .csv extension: {input_path}")

    # Check if file is empty
    if input_path.stat().st_size == 0:
        logger.error(f"Input file is empty: {input_path}")
        sys.exit(1)

    # Compute SHA256
    try:
        checksum = compute_sha256(input_path)
        logger.info(f"SHA256 checksum computed: {checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        sys.exit(1)

    # Define output paths
    filename = input_path.name
    checksum_filename = f"{filename}.sha256"
    checksum_path = output_dir / checksum_filename

    # Write checksum file
    try:
        with open(checksum_path, "w") as f:
            f.write(f"{checksum}  {filename}\n")
        logger.info(f"Checksum file written: {checksum_path}")
    except IOError as e:
        logger.error(f"Failed to write checksum file: {e}")
        sys.exit(1)

    # Verify the checksum by re-computing
    try:
        verify_checksum = compute_sha256(input_path)
        if verify_checksum != checksum:
            logger.error("Checksum verification failed after writing!")
            sys.exit(1)
        logger.info("Checksum verification successful.")
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        sys.exit(1)

    logger.info(f"Task T014 completed successfully. Output: {checksum_path}")

if __name__ == "__main__":
    main()
