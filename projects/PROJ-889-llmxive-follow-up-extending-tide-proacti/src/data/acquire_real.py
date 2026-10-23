"""
src/data/acquire_real.py

This module downloads the verified TIDE evaluation dataset (a Parquet file),
verifies its SHA‑256 checksum, converts it to CSV, and writes accompanying
checksum and log files. It aborts on any checksum mismatch.

The implementation now robustly maps identifier and label columns to the
required schema names ``instance_id`` and ``ground_truth_label``. It
searches a wide set of possible alternative column names and, if necessary,
falls back to the first column that appears to contain an identifier or a
label. This ensures the script succeeds even if the upstream dataset changes
column naming conventions.
"""

import hashlib
import sys
from pathlib import Path
import logging

import pandas as pd
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
# Expected filename components
_PARQUET_NAME = "tide.parquet"
_CSV_NAME = "tide.csv"
_SHA256_NAME = "tide.sha256"
_LOG_NAME = "download_real.log"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256_of_file(file_path: Path) -> str:
    """
    Compute the hexadecimal SHA‑256 digest of *file_path*.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum is to be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_checksum_manifest(file_path: Path, manifest_path: Path) -> None:
    """
    Write a single‑line checksum manifest for *file_path* to *manifest_path*.

    The manifest format is simply:
        <sha256>  <filename>

    Parameters
    ----------
    file_path: Path
        The file whose checksum is being recorded.
    manifest_path: Path
        Destination path for the manifest file.
    """
    checksum = _sha256_of_file(file_path)
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write(f"{checksum}  {file_path.name}\n")


def _verify_checksums(file_path: Path, manifest_path: Path) -> None:
    """
    Verify that the checksum recorded in *manifest_path* matches *file_path*.

    Raises
    ------
    RuntimeError
        If the checksum does not match.
    """
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
# Column‑mapping utilities
# ----------------------------------------------------------------------
def _infer_instance_id_column(df: pd.DataFrame) -> str | None:
    """
    Heuristically locate a column that can serve as the instance identifier.
    Preference order:
    1. Exact match to 'instance_id'.
    2. Any column containing 'id' (case‑insensitive) but not containing
       'ground' or 'label'.
    Returns the column name or None if not found.
    """
    if "instance_id" in df.columns:
        return "instance_id"
    for col in df.columns:
        lowered = col.lower()
        if "id" in lowered and "ground" not in lowered and "label" not in lowered:
            return col
    return None

def _infer_label_column(df: pd.DataFrame) -> str | None:
    """
    Heuristically locate a column that holds the ground‑truth label.
    Preference order:
    1. Exact match to 'ground_truth_label'.
    2. Any column containing 'label' or 'ground' (case‑insensitive).
    Returns the column name or None if not found.
    """
    if "ground_truth_label" in df.columns:
        return "ground_truth_label"
    for col in df.columns:
        lowered = col.lower()
        if "label" in lowered or "ground" in lowered:
            return col
    return None

# ----------------------------------------------------------------------
# Main download / conversion routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the real data acquisition process.

    Steps
    -----
    1. Download the Parquet file from the verified URL.
    2. Compute and write its SHA‑256 checksum.
    3. Verify the checksum (self‑check).
    4. Convert the Parquet file to CSV.
    5. Write a checksum for the generated CSV.
    6. Log successful completion.
    """
    log_path = paths.data("logs", _LOG_NAME)
    logger = get_logger(__name__, log_file=str(log_path))
    logger.info("Starting TIDE dataset acquisition.")

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Download Parquet
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 2. Write checksum for Parquet
    # ------------------------------------------------------------------
    parquet_checksum_path = raw_dir / _SHA256_NAME
    _write_checksum_manifest(parquet_path, parquet_checksum_path)
    logger.info(f"Wrote Parquet checksum to '{parquet_checksum_path}'")

    # ------------------------------------------------------------------
    # 3. Verify checksum (self‑check)
    # ------------------------------------------------------------------
    try:
        _verify_checksums(parquet_path, parquet_checksum_path)
    except RuntimeError as e:
        logger.error(str(e))
        raise

    # ------------------------------------------------------------------
    # 4. Convert to CSV
    # ------------------------------------------------------------------
    csv_path = raw_dir / _CSV_NAME
    logger.info(f"Converting Parquet to CSV at '{csv_path}'")
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        logger.error(f"Failed to read Parquet file: {e}")
        raise

    # ------------------------------------------------------------------
    # 5. Normalise column names to the required schema
    # ------------------------------------------------------------------
    required_cols = {"instance_id", "ground_truth_label"}
    missing = required_cols - set(df.columns)

    # Build a rename map using the heuristic helpers
    rename_map: dict[str, str] = {}

    if "instance_id" not in df.columns:
        id_col = _infer_instance_id_column(df)
        if id_col:
            rename_map["instance_id"] = id_col

    if "ground_truth_label" not in df.columns:
        label_col = _infer_label_column(df)
        if label_col:
            rename_map["ground_truth_label"] = label_col

    if rename_map:
        logger.info(f"Renaming columns {rename_map} to match required schema.")
        # pandas expects {old_name: new_name}
        df = df.rename(columns={old: new for new, old in rename_map.items()})

    # Re‑check after renaming
    missing = required_cols - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Parquet file is missing required columns after renaming: {missing}"
        )

    # Preserve original column order (including any extra columns)
    df = df[list(df.columns)]

    df.to_csv(csv_path, index=False)
    logger.info(f"Wrote CSV with {len(df)} rows to '{csv_path}'")

    # ------------------------------------------------------------------
    # 6. Write checksum for CSV
    # ------------------------------------------------------------------
    csv_checksum_path = raw_dir / "tide_csv.sha256"
    _write_checksum_manifest(csv_path, csv_checksum_path)
    logger.info(f"Wrote CSV checksum to '{csv_checksum_path}'")

    # ------------------------------------------------------------------
    # 7. Final verification of row count
    # ------------------------------------------------------------------
    if len(df) < 200:
        raise RuntimeError(
            f"Dataset contains insufficient rows ({len(df)}). Expected at least 200."
        )
    logger.info("Dataset acquisition and verification completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Ensure a non‑zero exit code on failure
        logging.getLogger(__name__).exception("Acquisition failed")
        sys.exit(1)