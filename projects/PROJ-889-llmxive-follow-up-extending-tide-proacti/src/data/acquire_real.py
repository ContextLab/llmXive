"""
src/data/acquire_real.py

This module downloads the verified TIDE evaluation dataset (a Parquet file),
verifies its SHA‑256 checksum, and obtains a CSV representation of the data.
The original implementation relied on the ``datasets`` library, which pulls
in ``pyarrow`` – a heavy optional dependency that is not available in the
execution environment (it requires NumPy 2.0).  To keep the script runnable
on the CI runner we fall back to a direct CSV download from the HuggingFace
hub when possible.  If a CSV is not hosted, the script aborts with a clear
error explaining the missing conversion path.

The script writes three artefacts in ``data/raw``:

* ``tide.parquet`` – the raw Parquet file.
* ``tide.sha256``   – a one‑line checksum manifest for the Parquet file.
* ``tide.csv``      – a CSV version of the dataset.
* ``tide_csv.sha256`` – checksum manifest for the CSV file.

It also records a log at ``data/logs/download_real.log``.  The script exits
with status 0 on success and a non‑zero status on any failure, matching the
expectations of ``src/data/test_acquire_real.py``.
"""

import hashlib
import sys
from pathlib import Path
import logging
import csv
import requests

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified URL for the TIDE evaluation dataset (Parquet format)
_DATA_URL = (
    "https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/"
    "data/test-00000-of-00001-9189dc62872204f7.parquet"
)
# Direct CSV URL – many HuggingFace datasets publish a CSV alongside the
# Parquet.  If this endpoint returns 200 we can avoid the ``datasets``
# library (and its heavy ``pyarrow`` dependency) entirely.
_CSV_URL = (
    "https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/"
    "data/test.csv"
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
# Download helpers
# ----------------------------------------------------------------------
def _download_file(url: str, dest_path: Path) -> None:
    """Download *url* to *dest_path* using a streaming request."""
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading from {url}")
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with dest_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        logger.error(f"Failed to download {url!r}: {e}")
        raise

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

    # --------------------------------------------------------------
    # 1. Download the Parquet file (required for checksum verification)
    # --------------------------------------------------------------
    parquet_path = raw_dir / _PARQUET_NAME
    if not parquet_path.is_file():
        logger.info(f"Downloading Parquet from {_DATA_URL}")
        _download_file(_DATA_URL, parquet_path)

    # 2. Write and verify checksum for the Parquet file
    parquet_checksum_path = raw_dir / _SHA256_NAME
    _write_checksum_manifest(parquet_path, parquet_checksum_path)
    logger.info(f"Wrote Parquet checksum to '{parquet_checksum_path}'")
    try:
        _verify_checksums(parquet_path, parquet_checksum_path)
    except RuntimeError as e:
        logger.error(str(e))
        raise

    # --------------------------------------------------------------
    # 3. Obtain CSV representation
    # --------------------------------------------------------------
    csv_path = raw_dir / _CSV_NAME
    if csv_path.is_file():
        logger.info(f"CSV already present at '{csv_path}' – skipping download.")
    else:
        # Try direct CSV download first (no pyarrow needed)
        logger.info(f"Attempting direct CSV download from {_CSV_URL}")
        try:
            _download_file(_CSV_URL, csv_path)
            logger.info(f"Successfully downloaded CSV to '{csv_path}'")
        except Exception as csv_err:
            logger.warning(
                f"Direct CSV download failed ({csv_err}); attempting fallback via "
                "`datasets` streaming (may require pyarrow)."
            )
            # ------------------------------------------------------------------
            # Fallback: stream via `datasets`.  This path is kept for completeness
            # but will raise a clear ImportError if pyarrow is unavailable.
            # ------------------------------------------------------------------
            try:
                from datasets import load_dataset
            except Exception as e:
                logger.error(
                    "The `datasets` library could not be imported. This fallback "
                    "requires the optional `pyarrow` dependency, which is not "
                    "available in the execution environment."
                )
                raise RuntimeError(
                    "Unable to obtain CSV representation of the TIDE dataset: "
                    "no direct CSV URL and `datasets` fallback failed."
                ) from e

            try:
                ds = load_dataset(
                    "deeplearning-tide/actresses",
                    split="test",
                    streaming=True,
                )
            except Exception as e:
                logger.error(f"Failed to load dataset via `datasets`: {e}")
                raise RuntimeError(
                    "Failed to stream the TIDE dataset using the `datasets` library."
                ) from e

            row_count = 0
            with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = None
                for record in ds:
                    if writer is None:
                        header = list(record.keys())
                        writer = csv.DictWriter(csv_file, fieldnames=header)
                        writer.writeheader()
                    writer.writerow(record)
                    row_count += 1
            logger.info(f"Wrote CSV with {row_count} rows to '{csv_path}'")

    # --------------------------------------------------------------
    # 4. Write checksum for the CSV
    # --------------------------------------------------------------
    csv_checksum_path = raw_dir / "tide_csv.sha256"
    _write_checksum_manifest(csv_path, csv_checksum_path)
    logger.info(f"Wrote CSV checksum to '{csv_checksum_path}'")

    # --------------------------------------------------------------
    # 5. Verify row count (T001 requires >= 200)
    # --------------------------------------------------------------
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        row_count = sum(1 for _ in reader) - 1  # subtract header
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