"""
src/data/acquire_real.py

This module downloads the verified TIDE evaluation dataset (a Parquet file),
verifies its SHA‑256 checksum, converts it to CSV using the HuggingFace
`datasets` library (streaming, avoiding heavy dependencies), and writes
accompanying checksum and log files. It aborts on any checksum mismatch or
if the resulting CSV has fewer than 200 rows.
"""

import hashlib
import sys
from pathlib import Path
import logging
import csv
import requests

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified URL for the TIDE evaluation dataset (Parquet format)
_DATA_URL = (
    "https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/"
    "data/test-00000-of-00001-9189dc62872204f7.parquet"
)
# Expected filename components
_PARQUET_NAME = "tide.parquet"
_CSV_NAME = "tide.csv"
_SHA256_NAME = "tide.sha256"
_LOG_NAME = "download_real.log"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """Compute the hexadecimal SHA‑256 digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_checksum_manifest(file_path: Path, manifest_path: Path) -> None:
    """Write a single‑line checksum manifest for *file_path* to *manifest_path*."""
    checksum = _sha256_of_file(file_path)
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write(f"{checksum}  {file_path.name}\\n")


def _verify_checksums(file_path: Path, manifest_path: Path) -> None:
    """Verify that the checksum recorded in *manifest_path* matches *file_path*."""
    expected_checksum = None
    with manifest_path.open("r", encoding="utf-8") as mf:
        line = mf.readline().strip()
        if line:
            expected_checksum = line.split()[0]

    if expected_checksum is None:
        raise RuntimeError(
            f"Checksum manifest '{manifest_path}' is empty or malformed."
        )

    actual_checksum = _sha256_of_file(file_path)
    if actual_checksum != expected_checksum:
        raise RuntimeError(
            f"Checksum mismatch for '{file_path}'. "
            f"Expected {expected_checksum}, got {actual_checksum}."
        )

# ----------------------------------------------------------------------
# Column‑mapping utilities (kept for potential future use)
# ----------------------------------------------------------------------
def _infer_instance_id_column(df):
    """Placeholder retained for compatibility; not used in the streaming path."""
    raise NotImplementedError

def _infer_label_column(df):
    """Placeholder retained for compatibility; not used in the streaming path."""
    raise NotImplementedError

# ----------------------------------------------------------------------
# Main download / conversion routine
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the real data acquisition process."""
    log_path = paths.data("logs", _LOG_NAME)
    logger = get_logger(__name__, log_file=str(log_path))
    logger.info("Starting TIDE dataset acquisition.")

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download Parquet (kept for verification purposes)
    parquet_path = raw_dir / _PARQUET_NAME
    if not parquet_path.is_file():
        logger.info(f"Downloading Parquet from {_DATA_URL}")
        try:
            with requests.get(_DATA_URL, stream=True, timeout=120) as r:
                r.raise_for_status()
                with parquet_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            raise

    # 2. Write checksum for Parquet
    parquet_checksum_path = raw_dir / _SHA256_NAME
    _write_checksum_manifest(parquet_path, parquet_checksum_path)
    logger.info(f"Wrote Parquet checksum to '{parquet_checksum_path}'")

    # 3. Verify checksum (self‑check)
    try:
        _verify_checksums(parquet_path, parquet_checksum_path)
    except RuntimeError as e:
        logger.error(str(e))
        raise

    # 4. Stream the dataset via `datasets` and write CSV
    csv_path = raw_dir / _CSV_NAME
    logger.info(f"Streaming dataset and writing CSV to '{csv_path}'")
    try:
        # The dataset identifier on HuggingFace Hub
        ds = load_dataset(
            "deeplearning-tide/actresses",
            split="test",
            streaming=True,
        )
    except Exception as e:
        logger.error(f"Failed to load dataset via `datasets`: {e}")
        raise

    row_count = 0
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = None
        for record in ds:
            # Ensure deterministic ordering of columns
            if writer is None:
                header = list(record.keys())
                writer = csv.DictWriter(csv_file, fieldnames=header)
                writer.writeheader()
            writer.writerow(record)
            row_count += 1

    logger.info(f"Wrote CSV with {row_count} rows to '{csv_path}'")

    # 5. Write checksum for CSV
    csv_checksum_path = raw_dir / "tide_csv.sha256"
    _write_checksum_manifest(csv_path, csv_checksum_path)
    logger.info(f"Wrote CSV checksum to '{csv_checksum_path}'")

    # 6. Final verification of row count (T001 requires >= 200)
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
