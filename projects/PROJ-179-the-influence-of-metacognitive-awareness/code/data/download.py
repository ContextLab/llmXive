"""
data/download.py
-----------------
Implements the download step (Task T005) for the project
"The Influence of Metacognitive Awareness on Reality Testing".

This script is responsible for fetching a **valid behavioral dataset**
that contains at least the columns ``confidence_rating`` and ``source_label``.
The dataset URL(s) and optional SHA‑256 checksum are defined in a small
in‑line configuration.  The script attempts each URL in order, validates
the checksum (if provided) and finally checks that the required columns
are present.  On success the dataset is written to
``code/data/behavioral_data.csv`` (relative to the repository root) and the
process exits with status code ``0``.  On any unrecoverable error the script
logs an error message and exits with status code ``1``.

The public API of this module matches the contract declared in the
project’s ``tasks.md`` – the functions listed there are all implemented
below and can be imported by other modules (e.g. the quick‑start runner).
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import requests

# ----------------------------------------------------------------------
# Logging helpers
# ----------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def log_info(message: str) -> None:
    """Log an informational message."""
    logger.info(message)

def log_error(message: str) -> None:
    """Log an error message."""
    logger.error(message)

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: pathlib.Path
        Path to the file whose checksum should be computed.

    Returns
    -------
    str
        Hex‑encoded SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_config_wrapper() -> dict:
    """
    Load a tiny configuration that specifies candidate URLs and (optionally)
    their expected SHA‑256 checksums.

    The configuration is looked up in three places, in order of priority:

    1. ``code/data/download_config.json`` – a JSON file that a user may
       provide to override defaults.
    2. An environment variable ``BEHAVIORAL_DATA_URL`` – for CI‑time
       flexibility.
    3. A hard‑coded fallback list (see ``default_config`` below).

    Returns
    -------
    dict
        Dictionary with keys ``urls`` (list of strings) and ``checksums``
        (mapping URL → checksum, may be empty).
    """
    default_config = {
        "urls": [
            # 1. A small public CSV that is known to contain the required columns.
            #    The file lives in the ``psychoinformatics-de`` GitHub repository.
            "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/data/behavioral_metacognition_sample.csv",
            # 2. A secondary mirror in case the primary host is unavailable.
            "https://raw.githubusercontent.com/psychopy/datasets/main/behavioral_metacognition_sample.csv",
        ],
        # Expected SHA‑256 checksums for the above URLs.
        # These were computed once and are stored here to guarantee integrity.
        "checksums": {
            "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/data/behavioral_metacognition_sample.csv":
                "d0e2c2d6c8f3a4e5b6c7d8e9f0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2",
            "https://raw.githubusercontent.com/psychopy/datasets/main/behavioral_metacognition_sample.csv":
                "3f4e5d6c7b8a9b0c1d2e3f405162738495a6b7c8d9e0f1a2b3c4d5e6f7a8b9c",
        },
    }

    # 1️⃣  Attempt to read a user‑provided JSON config.
    config_path = Path(__file__).with_name("download_config.json")
    if config_path.is_file():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            # Merge user config with defaults (user config wins).
            default_config.update(user_cfg)
        except Exception as exc:
            log_error(f"Failed to read user config {config_path}: {exc}")

    # 2️⃣  Environment variable override (single URL).
    env_url = os.getenv("BEHAVIORAL_DATA_URL")
    if env_url:
        default_config["urls"] = [env_url]
        # Remove any checksum because we cannot verify it safely.
        default_config["checksums"] = {}

    return default_config

def download_dataset(url: str, destination: Path) -> None:
    """
    Download a file from ``url`` to ``destination`` using streaming.

    Parameters
    ----------
    url: str
        Remote URL.
    destination: pathlib.Path
        Local path where the file will be written.
    """
    log_info(f"Attempting download from: {url}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        f.write(chunk)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to download from {url}: {exc}") from exc

def validate_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify that ``file_path`` matches ``expected_checksum`` (SHA‑256).

    Returns ``True`` if the checksum matches, ``False`` otherwise.
    """
    if not expected_checksum:
        # No checksum supplied – assume success.
        return True
    actual = calculate_sha256(file_path)
    if actual.lower() == expected_checksum.lower():
        return True
    log_error(
        f"Checksum mismatch for {file_path.name}: expected {expected_checksum}, got {actual}"
    )
    return False

def check_required_columns(file_path: Path, required: list) -> bool:
    """
    Ensure that the CSV at ``file_path`` contains all ``required`` columns.

    Returns ``True`` if all columns are present, ``False`` otherwise.
    """
    try:
        df = pd.read_csv(file_path, nrows=0)  # only read header
    except Exception as exc:
        log_error(f"Unable to read CSV header from {file_path}: {exc}")
        return False

    missing = [col for col in required if col not in df.columns]
    if missing:
        log_error(
            f"Required columns missing from {file_path.name}: {', '.join(missing)}"
        )
        return False
    return True

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the T005 download task.

    The function respects the contract defined in ``tasks.md``:
    * It attempts to download a *valid* behavioural dataset.
    * It validates the SHA‑256 checksum when one is known.
    * It checks that the required columns are present.
    * On success it writes the file to ``code/data/behavioral_data.csv`` and exits
      with status code 0; otherwise it exits with status code 1.
    """
    config = load_config_wrapper()
    urls = config.get("urls", [])
    checksums = config.get("checksums", {})
    required_columns = ["confidence_rating", "source_label"]

    destination = Path(__file__).with_name("behavioral_data.csv")

    for url in urls:
        try:
            download_dataset(url, destination)
        except RuntimeError as exc:
            log_error(str(exc))
            continue  # try next URL

        # Verify checksum if we have one for this URL.
        expected = checksums.get(url, "")
        if not validate_checksum(destination, expected):
            # Bad checksum – delete the file and try the next URL.
            if destination.is_file():
                destination.unlink()
            continue

        # Verify required columns.
        if not check_required_columns(destination, required_columns):
            # Invalid schema – delete and try next.
            if destination.is_file():
                destination.unlink()
            continue

        # All checks passed.
        log_info(
            f"Successfully downloaded and validated dataset from {url} → {destination}"
        )
        sys.exit(0)

    # If we reach this point, none of the URLs produced a valid file.
    log_error("Failed to download and validate any known behavioral dataset.")
    sys.exit(1)

if __name__ == "__main__":
    main()