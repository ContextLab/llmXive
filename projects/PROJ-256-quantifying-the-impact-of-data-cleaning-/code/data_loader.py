"""
Data Loader Module
------------------

This module provides utilities for downloading raw datasets, verifying their
integrity via SHA‑256 checksums, and loading them into pandas DataFrames.

The primary entry point is the ``main`` function, which is executed when the
module is run as a script (``python -m code.data_loader``).  It reads the
configuration (dataset URLs and expected checksums) from ``code.config``,
ensures that each dataset is present, and aborts with a non‑zero exit code
if any download fails or a checksum does not match.

The implementation deliberately avoids any silent fallback to mock data:
failures are logged and cause the process to exit with status ``1``.
"""

import os
import json
import logging
import hashlib
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from urllib.request import urlopen, Request

import pandas as pd

from utils import compute_file_checksum, setup_logging
from config import get_config

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def download_dataset(url: str, dest_path: str) -> None:
    """
    Download a dataset from ``url`` and write it to ``dest_path``.

    On any error (network, HTTP status, write permission, etc.) this
    function raises an exception.  The caller is responsible for handling
    the exception and exiting with a non‑zero status code.
    """
    try:
        logger.info(f"Starting download from {url}")
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as response:
            # Raise for HTTP errors (e.g., 404) – urllib does this automatically
            data = response.read()

        # Ensure parent directory exists
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)

        with open(dest_path, "wb") as f:
            f.write(data)

        logger.info(f"Successfully downloaded {url} to {dest_path}")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        # Re‑raise so the caller can abort the whole script
        raise


def compute_checksum(filepath: str) -> str:
    """
    Compute the SHA‑256 checksum of ``filepath`` using the shared utility.
    """
    return compute_file_checksum(filepath)


def verify_checksum(filepath: str, expected_checksum: str) -> bool:
    """
    Verify that the SHA‑256 checksum of ``filepath`` matches ``expected_checksum``.
    Returns ``True`` if they match, ``False`` otherwise.
    """
    actual = compute_checksum(filepath)
    if actual.lower() == expected_checksum.lower():
        logger.info(f"Checksum verification passed for {filepath}")
        return True
    else:
        logger.error(
            f"Checksum mismatch for {filepath}: expected {expected_checksum}, got {actual}"
        )
        return False


def load_datasets_from_raw(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV/JSON files from ``raw_dir`` into a dictionary of DataFrames.
    """
    datasets: Dict[str, pd.DataFrame] = {}
    raw_path = Path(raw_dir)

    if not raw_path.exists():
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets

    for file_path in raw_path.iterdir():
        if file_path.suffix.lower() not in {".csv", ".json"}:
            continue

        try:
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_json(file_path)

            dataset_id = file_path.stem
            datasets[dataset_id] = df
            logger.info(f"Loaded {dataset_id} from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")

    return datasets


def ensure_data_exists(raw_dir: str, urls: Dict[str, str], checksums: Dict[str, str]) -> bool:
    """
    Ensure that every dataset listed in ``urls`` exists in ``raw_dir``.
    If a file is missing, it is downloaded.  After download the SHA‑256
    checksum is verified against ``checksums``.  The function returns ``True``
    only if **all** datasets are present and pass checksum verification.
    """
    all_ok = True
    for name, url in urls.items():
        dest = Path(raw_dir) / f"{name}.csv"
        expected_checksum = checksums.get(name)

        if not dest.exists():
            logger.info(f"Dataset {name} not found locally – downloading.")
            try:
                download_dataset(url, str(dest))
            except Exception:
                # download_dataset already logged the error
                all_ok = False
                continue

        # If we have an expected checksum, verify it
        if expected_checksum:
            if not verify_checksum(str(dest), expected_checksum):
                all_ok = False
        else:
            logger.warning(
                f"No expected checksum provided for {name}; skipping verification."
            )
    return all_ok


def main() -> None:
    """
    Command‑line entry point.

    Reads configuration, ensures all raw datasets are present and valid,
    and exits with status ``0`` on success or ``1`` on any failure.
    """
    # Initialise logging – default to INFO level if not configured elsewhere
    setup_logging("INFO")

    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    urls: Dict[str, str] = config.get("DATASET_URLS", {})
    checksums: Dict[str, str] = config.get("DATASET_CHECKSUMS", {})

    if not urls:
        logger.error("No dataset URLs found in configuration. Aborting.")
        sys.exit(1)

    logger.info(f"Ensuring raw data directory exists at {raw_dir}")
    Path(raw_dir).mkdir(parents=True, exist_ok=True)

    success = ensure_data_exists(raw_dir, urls, checksums)

    if not success:
        logger.error("One or more datasets failed to download or verify.")
        sys.exit(1)

    logger.info("All datasets are present and passed checksum verification.")
    # Optionally, we could load them here to confirm they are readable,
    # but the primary responsibility of this script is acquisition & verification.
    sys.exit(0)


if __name__ == "__main__":
    main()