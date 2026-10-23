"""
src/data/acquire_real.py

Revised implementation for T001.

This script downloads the verified TIDE evaluation dataset from the HuggingFace
Hub using the ``huggingface_hub`` utility (which works for public datasets
without requiring the heavy ``pyarrow`` dependency).  It fetches both the
original Parquet file and the CSV representation, writes SHA‑256 checksum
manifests for each, and validates that the CSV contains at least 200 data
rows (excluding the header).  All artefacts are written under ``data/raw``.
Logging is performed via ``llmxive_toolkit.get_logger`` and written to
``data/logs/download_real.log``.
"""

import hashlib
import logging
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download, RepositoryNotFoundError

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ID = "deeplearning-tide/tide"
PARQUET_FILE = "data/test-00000-of-00001-9189dc62872204f7.parquet"
CSV_FILE = "data/test.csv"

PARQUET_NAME = "tide.parquet"
CSV_NAME = "tide.csv"
PARQUET_SHA_NAME = "tide.sha256"
CSV_SHA_NAME = "tide_csv.sha256"
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


def _verify_checksum(file_path: Path, manifest_path: Path) -> None:
    """Raise RuntimeError if the checksum in *manifest_path* does not match *file_path*."""
    with manifest_path.open("r", encoding="utf-8") as mf:
        line = mf.readline().strip()
    if not line:
        raise RuntimeError(f"Checksum manifest '{manifest_path}' is empty or malformed.")
    expected = line.split()[0]
    actual = _sha256_of_file(file_path)
    if actual != expected:
        raise RuntimeError(
            f"Checksum mismatch for '{file_path}'. Expected {expected}, got {actual}."
        )


# ----------------------------------------------------------------------
# Download routine using huggingface_hub
# ----------------------------------------------------------------------
def _download_from_hub(filename: str, dest_path: Path) -> None:
    """
    Download *filename* from the TIDE dataset repo to *dest_path*.

    ``hf_hub_download`` raises ``RepositoryNotFoundError`` if the repository
    or the file cannot be accessed (e.g., private repo).  Any other exception
    is re‑raised after logging.
    """
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Downloading '{filename}' from HuggingFace Hub.")
        cached_path = hf_hub_download(repo_id=REPO_ID, filename=filename, repo_type="dataset")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        # Copy the cached file to the desired location
        dest_path.write_bytes(Path(cached_path).read_bytes())
    except RepositoryNotFoundError as e:
        logger.error(f"Repository or file not found: {e}")
        raise RuntimeError(f"Could not locate '{filename}' in repo '{REPO_ID}'.") from e
    except Exception as e:
        logger.error(f"Failed to download '{filename}': {e}")
        raise


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the real data acquisition process."""
    log_path = paths.data("logs", LOG_NAME)
    logger = get_logger(__name__, log_file=str(log_path))
    logger.info("Starting TIDE dataset acquisition (via HuggingFace Hub).")

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # 1. Download Parquet and verify checksum
    # --------------------------------------------------------------
    parquet_path = raw_dir / PARQUET_NAME
    if not parquet_path.is_file():
        _download_from_hub(PARQUET_FILE, parquet_path)

    parquet_checksum_path = raw_dir / PARQUET_SHA_NAME
    _write_checksum(parquet_path, parquet_checksum_path)
    logger.info(f"Wrote Parquet checksum to '{parquet_checksum_path}'.")
    _verify_checksum(parquet_path, parquet_checksum_path)
    logger.info("Parquet checksum verified.")

    # --------------------------------------------------------------
    # 2. Download CSV and verify checksum
    # --------------------------------------------------------------
    csv_path = raw_dir / CSV_NAME
    if not csv_path.is_file():
        _download_from_hub(CSV_FILE, csv_path)

    csv_checksum_path = raw_dir / CSV_SHA_NAME
    _write_checksum(csv_path, csv_checksum_path)
    logger.info(f"Wrote CSV checksum to '{csv_checksum_path}'.")
    _verify_checksum(csv_path, csv_checksum_path)
    logger.info("CSV checksum verified.")

    # --------------------------------------------------------------
    # 3. Validate row count (must be >= 200)
    # --------------------------------------------------------------
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to read CSV '{csv_path}': {e}")
        raise RuntimeError(f"Unable to parse CSV at '{csv_path}'.") from e

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
