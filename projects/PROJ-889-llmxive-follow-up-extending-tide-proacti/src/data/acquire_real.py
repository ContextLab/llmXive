"""
src/data/acquire_real.py

Implementation for T001.
This script downloads the TIDE evaluation dataset from the HuggingFace Hub,
writes it to 'data/raw/tide.csv', and creates a SHA-256 checksum manifest
'data/raw/tide.sha256'.

Verification:
- CSV contains >= 200 rows.
- Checksum file matches the SHA-256 of tide.csv.
- Log records successful download and validation.
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
# Per plan.md: use the verified TIDE dataset
REPO_ID = "deeplearning-tide/tide"
SPLIT = "test"
CSV_NAME = "tide.csv"
CSV_SHA_NAME = "tide.sha256"
LOG_NAME = "acquire_real.log"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA-256 digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_checksum(file_path: Path, manifest_path: Path) -> None:
    """Write a single-line checksum manifest for *file_path*."""
    checksum = _sha256_of_file(file_path)
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write(f"{checksum}  {file_path.name}\n")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the real data acquisition process."""
    log_path = paths.data("logs", LOG_NAME)
    logger = get_logger(__name__, log_file=str(log_path))
    logger.info(f"Starting dataset acquisition using {REPO_ID} (split={SPLIT}).")

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / CSV_NAME
    checksum_path = raw_dir / CSV_SHA_NAME

    # --------------------------------------------------------------
    # 1. Load the dataset using the datasets library (streaming).
    # --------------------------------------------------------------
    try:
        logger.info(f"Streaming dataset '{REPO_ID}' split '{SPLIT}'.")
        # Use streaming=True as per plan.md to handle potentially large datasets
        dataset = load_dataset(REPO_ID, split=SPLIT, streaming=True, trust_remote_code=True)

        # Convert the streamed dataset to a list of records
        records = list(dataset)
        df = pd.DataFrame(records)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        # Fail loudly as per Core Constraint 9
        raise RuntimeError(f"Could not load dataset '{REPO_ID}'. Ensure it is public and reachable.") from e

    # --------------------------------------------------------------
    # 2. Map to TIDE schema and write CSV.
    # --------------------------------------------------------------
    try:
        # Expected schema: instance_id, code, ground_truth_label
        # If 'instance_id' is missing, generate it.
        if "instance_id" not in df.columns:
            df.insert(0, "instance_id", range(len(df)))

        # Map labels if necessary (e.g., 'label' -> 'ground_truth_label')
        if "label" in df.columns and "ground_truth_label" not in df.columns:
            df = df.rename(columns={"label": "ground_truth_label"})

        # Ensure required columns exist
        required = {"instance_id", "code", "ground_truth_label"}
        missing = required - set(df.columns)
        if missing:
            logger.error(f"Dataset missing required columns: {missing}. Found: {df.columns.tolist()}")
            raise RuntimeError(f"Dataset does not contain required columns: {missing}")

        # Keep only required columns for the raw CSV
        processed_df = df[list(required)]
        processed_df.to_csv(csv_path, index=False)
        logger.info(f"Wrote CSV to '{csv_path}'.")
    except Exception as e:
        logger.error(f"Failed to process/write CSV: {e}")
        raise RuntimeError(f"Could not write CSV to '{csv_path}'.") from e

    # --------------------------------------------------------------
    # 3. Write and verify checksum.
    # --------------------------------------------------------------
    _write_checksum(csv_path, checksum_path)
    logger.info(f"Wrote checksum to '{checksum_path}'.")

    try:
        with checksum_path.open("r", encoding="utf-8") as mf:
            line = mf.readline().strip()
        if not line:
            raise RuntimeError("Checksum file is empty.")
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
    row_count = len(processed_df)
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