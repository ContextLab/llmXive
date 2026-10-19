"""
download.py
-------------
This script implements both the **download** of the SubseasonalRodeo dataset
and the **Data Availability Gate** required by task T001/T002.

- ``download_dataset()`` downloads the verified archive from HuggingFace,
  streams it to ``data/raw/subseasonal_rodeo.tar.gz`` and verifies the
  SHA‑256 checksum (using a side‑car ``.sha256`` file if present, otherwise
  it creates the checksum file for future runs).
- ``data_availability_gate()`` scans the extracted parquet files under
  ``data/raw`` and ensures that at least one required probability field
  (``probability_value`` or ``precip_prob``) is present.  If not, it logs an
  error and exits with status code 1.

The script can be invoked from the command line:

``python -m src.download download``   – performs the download step
``python -m src.download verify``    – runs the data‑availability gate
``python -m src.download`` (default) – runs the gate

The two shell wrappers ``data/download.sh`` and ``data/verify.sh`` (added
as separate artifacts) simply call the appropriate entry points.
"""

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
import requests

from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified URL for the SubseasonalRodeo dataset archive.
# This URL points to the canonical HuggingFace repository.
SUBSEASONAL_RODEO_URL = (
    "https://huggingface.co/datasets/subseasonal_rodeo/resolve/main/subseasonal_rodeo.tar.gz"
)
# Destination path for the downloaded archive.
ARCHIVE_PATH = paths.data("raw", "subseasonal_rodeo.tar.gz")
# Path for the checksum side‑car file.
CHECKSUM_PATH = ARCHIVE_PATH.with_suffix(".sha256")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _find_parquet_files(root: Path):
    """
    Recursively locate all ``*.parquet`` files under the given root directory.
    """
    parquet_files = list(root.rglob("*.parquet"))
    if not parquet_files:
        log.error(f"No parquet files found under {root}")
    return parquet_files

def _has_required_field(df_columns: set) -> bool:
    """
    Return ``True`` if the column set contains either ``probability_value``
    or ``precip_prob``.
    """
    required = {"probability_value", "precip_prob"}
    return bool(required.intersection(df_columns))

# ----------------------------------------------------------------------
# Data Availability Gate
# ----------------------------------------------------------------------
def data_availability_gate() -> None:
    """
    Perform the Data Availability Gate check.

    - Scans all parquet files in ``data/raw``.
    - If any file contains at least one of the required fields, the gate
      passes and the script exits with code 0.
    - Otherwise, logs an error and exits with code 1.
    """
    raw_dir = paths.data("raw")
    if not raw_dir.exists():
        log.error(f"Raw data directory does not exist: {raw_dir}")
        sys.exit(1)

    parquet_files = _find_parquet_files(raw_dir)
    if not parquet_files:
        log.error("Data Availability Gate Failed: no parquet files to inspect.")
        sys.exit(1)

    for parquet_path in parquet_files:
        try:
            # Load only the column names – reading the full file is acceptable for
            # the typical SubseasonalRodeo parquet size.
            df = pd.read_parquet(parquet_path)
        except Exception as exc:
            log.error(f"Failed to read parquet file {parquet_path}: {exc}")
            sys.exit(1)

        cols = set(df.columns)
        if _has_required_field(cols):
            log.info(
                f"Data Availability Gate passed – required field found in "
                f"{parquet_path.name}"
            )
            # Successful gate; exit with 0.
            return

    # If we reach this point, none of the files contained the required fields.
    log.error("Data Availability Gate Failed")
    sys.exit(1)

# ----------------------------------------------------------------------
# Download routine
# ----------------------------------------------------------------------
def download_dataset(url: str = SUBSEASONAL_RODEO_URL, out_path: Path = ARCHIVE_PATH) -> None:
    """
    Download the SubseasonalRodeo archive, verify its SHA‑256 checksum,
    and write it to ``out_path``.

    If a ``.sha256`` file already exists next to the archive, its contents
    are treated as the expected checksum.  A mismatch raises ``ValueError``.
    If the side‑car does not exist, the computed checksum is written to it
    for future verification.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"Starting download from {url}")

    sha256 = hashlib.sha256()
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with out_path.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    sha256.update(chunk)
    except Exception as exc:
        log.error(f"Failed to download dataset: {exc}")
        raise

    computed_checksum = sha256.hexdigest()
    log.info(f"Download completed – SHA256: {computed_checksum}")

    # Verify against existing checksum file if present
    if CHECKSUM_PATH.exists():
        expected_checksum = CHECKSUM_PATH.read_text().strip()
        if expected_checksum.lower() != computed_checksum.lower():
            raise ValueError(
                f"Checksum mismatch for {out_path.name}: "
                f"expected {expected_checksum}, got {computed_checksum}"
            )
        else:
            log.info("Checksum verification passed (matched existing .sha256 file).")
    else:
        # No checksum file yet – write one for future runs
        CHECKSUM_PATH.write_text(computed_checksum)
        log.info(f"Wrote checksum to {CHECKSUM_PATH}")

# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def _parse_args():
    parser = argparse.ArgumentParser(
        description="Download SubseasonalRodeo dataset and/or run the Data Availability Gate."
    )
    subparsers = parser.add_subparsers(dest="command")

    download_parser = subparsers.add_parser(
        "download", help="Download the dataset archive."
    )
    download_parser.add_argument(
        "--url",
        type=str,
        default=SUBSEASONAL_RODEO_URL,
        help="URL of the dataset tar.gz archive.",
    )
    download_parser.add_argument(
        "--out",
        type=str,
        default=str(ARCHIVE_PATH),
        help="Path to write the downloaded archive.",
    )

    subparsers.add_parser("verify", help="Run the Data Availability Gate.")

    # If no sub‑command is supplied we default to the gate (historical behaviour)
    return parser.parse_args()

def main():
    args = _parse_args()
    if args.command == "download":
        # Resolve paths from possible string arguments
        out_path = Path(args.out)
        download_dataset(url=args.url, out_path=out_path)
    else:
        # Default / verify command runs the gate
        data_availability_gate()

if __name__ == "__main__":
    main()
