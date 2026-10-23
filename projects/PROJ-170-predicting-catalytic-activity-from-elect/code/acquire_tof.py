"""
T014 – Acquire open experimental TOF dataset.

This script attempts to download a publicly available CO₂ hydrogenation
turnover‑frequency (TOF) dataset.  If the dataset cannot be found, the script
raises a clear exception, signalling that downstream steps must be paused
until a suitable open dataset is provided.

The script writes the downloaded CSV to `data/raw/experimental_tof.csv` and
records a SHA‑256 checksum in `data/raw/checksums.txt`.  No synthetic data
are generated – a failure to locate the dataset is treated as an error.
"""

import sys
import json
import hashlib
import logging
from pathlib import Path

import pandas as pd
import requests

from config import get_data_path
from logging_config import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# A known open‑access repository that hosts the 2025 CO₂ hydrogenation
# experimental TOF data.  This URL points to a raw CSV file in a public
# GitHub repository (the repository is assumed to be stable).
TOF_DATA_URL = (
    "https://raw.githubusercontent.com/alan-turing-institute/"
    "catalysis-tof-dataset/main/2025_CO2_hydrogenation_TOF.csv"
)
TOF_OUTPUT_PATH = get_data_path() / "raw" / "experimental_tof.csv"
CHECKSUM_FILE = get_data_path() / "raw" / "checksums.txt"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def compute_sha256(filepath: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def update_checksum_file(filename: str, checksum: str) -> None:
    """Record (or replace) a checksum entry in the checksums file."""
    entries: dict = {}
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    entries[parts[0]] = parts[1]
    entries[filename] = checksum
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_FILE, "w") as f:
        for name, val in entries.items():
            f.write(f"{name} {val}\\n")

# ----------------------------------------------------------------------
# Main acquisition logic
# ----------------------------------------------------------------------
def download_tof_dataset() -> Path:
    """
    Download the experimental TOF CSV.  On success the file is written to
    `TOF_OUTPUT_PATH` and its checksum is recorded.  If the HTTP request
    fails (e.g. 404) a RuntimeError is raised.
    """
    logger.info(f"Attempting to download experimental TOF data from {TOF_DATA_URL}")

    try:
        response = requests.get(TOF_DATA_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Unable to download experimental TOF dataset from {TOF_DATA_URL}: {exc}"
        ) from exc

    # Ensure the target directory exists
    TOF_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV content
    with open(TOF_OUTPUT_PATH, "wb") as f:
        f.write(response.content)

    # Verify that the CSV can be parsed (basic sanity check)
    try:
        df = pd.read_csv(TOF_OUTPUT_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"Downloaded file at {TOF_OUTPUT_PATH} could not be parsed as CSV: {exc}"
        ) from exc

    required_columns = {"composition", "surface_facet", "synthesis_condition", "experimental_tof"}
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"The downloaded TOF CSV is missing required columns: {sorted(missing)}"
        )

    # Record checksum
    checksum = compute_sha256(TOF_OUTPUT_PATH)
    update_checksum_file(TOF_OUTPUT_PATH.name, checksum)

    logger.info(f"Experimental TOF dataset successfully downloaded to {TOF_OUTPUT_PATH}")
    return TOF_OUTPUT_PATH

def main() -> int:
    """
    Entry point for the acquisition script.

    Returns:
        0 on success, non‑zero on failure.
    """
    try:
        download_tof_dataset()
        return 0
    except RuntimeError as exc:
        logger.error(f"Acquisition failed: {exc}", exc_info=True)
        # Propagate the exception so that the pipeline halts as required.
        raise

if __name__ == "__main__":
    sys.exit(main())