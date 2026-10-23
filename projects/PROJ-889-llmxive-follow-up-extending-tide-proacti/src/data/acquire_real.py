"""
src/data/acquire_real.py

Revised implementation for T001.

This script downloads the verified TIDE evaluation dataset from the HuggingFace Hub
using the ``datasets`` library (which handles both parquet and CSV formats).  It writes
a CSV representation to ``data/raw/tide.csv`` and creates a SHA‑256 checksum manifest
``data/raw/tide.sha256``.  The script validates that the CSV contains at least 200 data
rows (excluding the header) and aborts with a clear error if this condition is not met.

Logging is performed via ``llmxive_toolkit.get_logger`` and written to
``data/logs/download_real.log``.
"""

import hashlib
import logging
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ID = "deeplearning-tide/tide"
SPLIT = "test"  # The dataset split containing evaluation instances
CSV_NAME = "tide.csv"
CSV_SHA_NAME = "tide.sha256"
LOG_NAME = "download_real.log"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_checksum(file_path: Path, manifest_path: Path) -> None:
    """Write a single‑line checksum manifest for *file_path*."""
    checksum = _sha256_of_file(file_path)
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write(f"{checksum}  {file_path.name}\\n")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the real data acquisition process."""
    log_path = paths.data("logs", LOG_NAME)
    logger = get_logger(__name__, log_file=str(log_path))
    logger.info("Starting TIDE dataset acquisition (via datasets library).")

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / CSV_NAME
    checksum_path = raw_dir / CSV_SHA_NAME

    # --------------------------------------------------------------
    # 1. Load the dataset using the ``datasets`` library.
    # --------------------------------------------------------------
    try:
        logger.info(f"Loading dataset '{REPO_ID}' split '{SPLIT}'.")
        dataset = load_dataset(REPO_ID, split=SPLIT)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(f"Could not load dataset '{REPO_ID}'.") from e

    # --------------------------------------------------------------
    # 2. Convert to pandas and write CSV.
    # --------------------------------------------------------------
    try:
        df: pd.DataFrame = dataset.to_pandas()
    except Exception as e:
        logger.error(f"Failed to convert dataset to pandas: {e}")
        raise RuntimeError("Dataset conversion to pandas failed.") from e

    try:
        df.to_csv(csv_path, index=False)
        logger.info(f"Wrote CSV to '{csv_path}'.")
    except Exception as e:
        logger.error(f"Failed to write CSV: {e}")
        raise RuntimeError(f"Could not write CSV to '{csv_path}'.") from e

    # --------------------------------------------------------------
    # 3. Write and verify checksum.
    # --------------------------------------------------------------
    _write_checksum(csv_path, checksum_path)
    logger.info(f"Wrote checksum to '{checksum_path}'.")

    # Verify checksum immediately (sanity check)
    try:
        with checksum_path.open("r", encoding="utf-8") as mf:
            line = mf.readline().strip()
        expected = line.split()[0]
        actual = _sha256_of_file(csv_path)
        if actual != expected:
            raise RuntimeError(
                f"Checksum mismatch for '{csv_path}'. Expected {expected}, got {actual}."
            )
        logger.info("Checksum verification passed.")
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        raise

    # --------------------------------------------------------------
    # 4. Validate row count (must be >= 200)
    # --------------------------------------------------------------
    row_count = len(df)
    logger.info(f"CSV row count (excluding header): {row_count}")

    if row_count < 200:
        raise RuntimeError(
            f"Dataset contains insufficient rows ({row_count}). Expected at least 200."
        )

    logger.info("Dataset acquisition and verification completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.getLogger(__name__).exception("Acquisition failed")
        sys.exit(1)
