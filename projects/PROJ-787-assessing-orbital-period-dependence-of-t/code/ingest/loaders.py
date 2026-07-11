"""
Data loaders for the exoplanet radius gap analysis pipeline.

This module provides utilities to load preprocessed and deduplicated datasets
into unified DataFrames for downstream analysis, with explicit checksum verification
to ensure data integrity (FR-001, Constitution Principle III).
"""

import os
import sys
import logging
import hashlib
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DEDUPED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "deduped_planets.csv"
CHECKSUM_FILE_PATH = PROJECT_ROOT / "data" / "processed" / "deduped_planets.csv.sha256"


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Checksum computation failed: File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
    except IOError as e:
        logger.error(f"Error reading file for checksum: {file_path}. Error: {e}")
        raise

    return hasher.hexdigest()


def verify_checksum(data_path: Path, checksum_path: Optional[Path] = None) -> bool:
    """
    Verify the checksum of a data file against a stored checksum.

    If no checksum file is provided, it attempts to find one adjacent to the data file
    with a '.sha256' extension. If the checksum file does not exist, verification
    is skipped and True is returned (with a warning).

    Args:
        data_path: Path to the data file.
        checksum_path: Optional path to the checksum file.

    Returns:
        True if checksums match, or if no checksum file exists (with warning).
        False if checksums do not match.

    Raises:
        FileNotFoundError: If the data file is missing.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    if checksum_path is None:
        checksum_path = data_path.with_suffix(data_path.suffix + ".sha256")

    if not checksum_path.exists():
        logger.warning(f"Checksum file not found at {checksum_path}. Skipping integrity check.")
        return True

    try:
        with open(checksum_path, "r", encoding="utf-8") as f:
            stored_checksum = f.read().strip().split()[0]  # Handle "checksum  filename" format
    except IOError as e:
        logger.error(f"Error reading checksum file: {checksum_path}. Error: {e}")
        raise

    current_checksum = compute_file_checksum(data_path)

    if current_checksum.lower() != stored_checksum.lower():
        logger.error(f"Checksum mismatch for {data_path}!")
        logger.error(f"  Expected: {stored_checksum}")
        logger.error(f"  Found:    {current_checksum}")
        return False

    logger.info(f"Checksum verified successfully for {data_path}")
    return True


def save_checksum(data_path: Path, checksum_path: Optional[Path] = None) -> str:
    """
    Compute and save the checksum of a data file.

    Args:
        data_path: Path to the data file.
        checksum_path: Optional path to save the checksum file. Defaults to data_path + '.sha256'.

    Returns:
        The computed checksum string.

    Raises:
        FileNotFoundError: If the data file is missing.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Cannot save checksum: Data file not found: {data_path}")

    if checksum_path is None:
        checksum_path = data_path.with_suffix(data_path.suffix + ".sha256")

    checksum = compute_file_checksum(data_path)

    try:
        with open(checksum_path, "w", encoding="utf-8") as f:
            f.write(f"{checksum}  {data_path.name}\n")
        logger.info(f"Checksum saved to {checksum_path}")
    except IOError as e:
        logger.error(f"Error writing checksum file: {checksum_path}. Error: {e}")
        raise

    return checksum


def load_deduplicated_planets(
    data_path: Optional[Path] = None,
    verify: bool = True,
    checksum_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load the deduplicated planets dataset into a unified DataFrame.

    This function loads the CSV file produced by T015 (preprocess.py),
    verifies its integrity via checksum if requested, and returns a
    pandas DataFrame ready for downstream analysis.

    Args:
        data_path: Path to the deduplicated CSV file. Defaults to data/processed/deduped_planets.csv.
        verify: If True, verify the file checksum before loading.
        checksum_path: Optional path to the checksum file. Defaults to data_path + '.sha256'.

    Returns:
        A pandas DataFrame containing the deduplicated planet records.

    Raises:
        FileNotFoundError: If the data file or checksum file is missing (when verify=True).
        ValueError: If checksum verification fails.
        pd.errors.EmptyDataError: If the file is empty.
    """
    if data_path is None:
        data_path = DEDUPED_DATA_PATH

    if not data_path.exists():
        raise FileNotFoundError(f"Input file not found: {data_path}")

    if verify:
        if not verify_checksum(data_path, checksum_path):
            raise ValueError(f"Data integrity check failed for {data_path}. Aborting load.")

    logger.info(f"Loading deduplicated planets from {data_path}")
    try:
        df = pd.read_csv(data_path)
    except pd.errors.EmptyDataError:
        logger.error(f"File {data_path} is empty.")
        raise
    except Exception as e:
        logger.error(f"Failed to load CSV from {data_path}: {e}")
        raise

    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df


def main():
    """
    Main entry point for testing the loader.
    Loads the deduplicated dataset and prints basic statistics.
    """
    logger.info("Starting loader test...")

    try:
        # Load the data
        df = load_deduplicated_planets()

        # Basic sanity checks
        required_columns = ["kepler_id", "pl_radj", "pl_radj_err1", "pl_orbper", "pl_orbper_err1"]
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            sys.exit(1)

        # Print summary
        logger.info("Data Summary:")
        logger.info(f"Total planets: {len(df)}")
        logger.info(f"Radius range: {df['pl_radj'].min():.2f} - {df['pl_radj'].max():.2f} Rjup")
        logger.info(f"Period range: {df['pl_orbper'].min():.2f} - {df['pl_orbper'].max():.2f} days")

        # Verify checksum generation if it doesn't exist
        if not CHECKSUM_FILE_PATH.exists():
            logger.info("Generating checksum file...")
            save_checksum(DEDUPED_DATA_PATH)
            logger.info("Checksum file generated.")

        logger.info("Loader test completed successfully.")
        return df

    except Exception as e:
        logger.error(f"Loader test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()