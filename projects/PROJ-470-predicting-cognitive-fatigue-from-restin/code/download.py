"""
Download and validate the Sleep‑EDF Expanded dataset.
Fetches the full dataset, validates variables, checks participant count (N ≥ 30),
and writes an atomic manifest to ``data/raw/download_manifest.json``.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Constants
DATASET_URL = "https://physionet.org/files/sleep-edfx/1.0.0/"
METADATA_URL = "https://physionet.org/api/files/sleep-edfx/1.0.0/"
OUTPUT_DIR = Path("data/raw")
MANIFEST_PATH = OUTPUT_DIR / "download_manifest.json"
VALIDATION_REPORT_PATH = Path("data/processed") / "validation_report.json"

# Required variables in the dataset
REQUIRED_VARIABLES = ["eeg_data", "fatigue_rating"]

# Minimum participants required
MIN_PARTICIPANTS = 30


def setup_logger(name: str = "download", log_file: str | None = None):
    """Simple logger setup."""
    import logging

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(fh)
    return logger


def check_metadata_availability(logger):
    """Perform HTTP HEAD request to metadata URL before downloading."""
    logger.info(f"Checking metadata availability at {METADATA_URL}...")
    try:
        req = Request(METADATA_URL, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0 (compatible; llmXive/1.0)")
        with urlopen(req, timeout=10) as response:
            if response.status == 200:
                logger.info("Metadata URL is accessible.")
                return True
            logger.error(f"Metadata URL returned status {response.status}")
            return False
    except HTTPError as e:
        logger.error(f"HTTP error checking metadata: {e.code} {e.reason}")
        return False
    except URLError as e:
        logger.error(f"URL error checking metadata: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking metadata: {e}")
        return False


def fetch_dataset(logger):
    """
    Fetch the Sleep‑EDF Expanded dataset using MNE‑Python.
    The function raises an error if fetching fails – no silent fallback.
    """
    logger.info("Attempting to fetch Sleep‑EDF Expanded dataset...")
    try:
        import mne
        from mne.datasets import sleep_edf

        # Fetch into the designated output directory
        data_path = sleep_edf.fetch_sleep_edf(path=str(OUTPUT_DIR), force_update=True)
        logger.info(f"Dataset fetched successfully to {data_path}")
        return data_path
    except ImportError:
        logger.error("MNE library not found. Cannot fetch real dataset.")
        raise RuntimeError(
            "MNE library required for fetching Sleep‑EDF dataset. Please install via requirements.txt."
        )
    except Exception as e:
        logger.error(f"Dataset fetch failed: {e}")
        raise RuntimeError(f"Dataset fetch failed: {e}")


def validate_variables(data_path, logger):
    """
    Validate the presence of required variables in the fetched data.
    The function raises ``ValueError`` if any required variable is missing.
    """
    logger.info("Validating variables in dataset...")
    if isinstance(data_path, str):
        data_path = Path(data_path)

    if not data_path.exists():
        raise FileNotFoundError(f"Data path does not exist: {data_path}")

    # Scan for EEG files – their presence implies ``eeg_data``.
    eeg_files = list(data_path.rglob("*.edf")) + list(data_path.rglob("*.fif"))
    has_eeg = bool(eeg_files)

    # Look for any file that might contain fatigue information.
    fatigue_files = list(data_path.rglob("*fatigue*")) + list(data_path.rglob("*rating*"))
    has_fatigue = bool(fatigue_files)

    available = []
    if has_eeg:
        available.append("eeg_data")
    if has_fatigue:
        available.append("fatigue_rating")

    missing = [v for v in REQUIRED_VARIABLES if v not in available]
    if missing:
        logger.error(f"Required variable(s) {missing} NOT found in dataset.")
        logger.error(f"Available variables: {available}")
        raise ValueError(
            f"Dataset missing required variable(s) {missing}. Available: {available}"
        )
    logger.info("Variables validated successfully.")
    return available


def count_participants(data_path, logger):
    """Count participants in the dataset based on unique EDF filenames."""
    logger.info("Counting participants...")
    if isinstance(data_path, str):
        data_path = Path(data_path)

    subjects = set()
    for f in data_path.rglob("*.edf"):
        name = f.stem
        subjects.add(name)
    n = len(subjects)
    logger.info(f"Found {n} participants.")
    return n


def save_dataset_to_disk(data_path, logger):
    """Placeholder – dataset is already on disk after fetch."""
    logger.info(f"Dataset is available at {data_path}")


def create_manifest(data_path, n_participants, variables, logger):
    """Create a manifest dictionary describing the downloaded dataset."""
    if isinstance(data_path, str):
        data_path = Path(data_path)

    files = [
        str(f.relative_to(data_path))
        for f in data_path.rglob("*.edf") + data_path.rglob("*.fif")
    ]

    manifest = {
        "dataset": "Sleep-EDF Expanded",
        "version": "1.0.0",
        "n_participants": n_participants,
        "variables_found": variables,
        "data_path": str(data_path),
        "files": files,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return manifest


def write_manifest_atomically(manifest, manifest_path, logger):
    """Write manifest atomically using a temporary file."""
    logger.info(f"Writing manifest atomically to {manifest_path}")
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(suffix=".json", dir=manifest_path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2)
        os.replace(temp_path, manifest_path)
        logger.info("Manifest written successfully.")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e


def write_validation_report(n_participants, variables, status, logger):
    """Write a validation report to ``data/processed/validation_report.json``."""
    report_path = Path("data/processed") / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "n_participants": n_participants,
        "variables_found": variables,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Download and validate EEG dataset.")
    parser.add_argument("--validate", action="store_true", help="Only validate existing data.")
    args = parser.parse_args()

    logger = setup_logger()

    # Ensure required directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # 1. Check metadata availability
    if not check_metadata_availability(logger):
        logger.error("Metadata check failed. Aborting.")
        sys.exit(1)

    # 2. Fetch dataset
    try:
        data_path = fetch_dataset(logger)
    except Exception as e:
        logger.error(f"Dataset fetch failed: {e}")
        sys.exit(1)

    # 3. Validate variables
    try:
        variables = validate_variables(data_path, logger)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # 4. Count participants
    try:
        n_participants = count_participants(data_path, logger)
    except Exception as e:
        logger.error(f"Participant count failed: {e}")
        sys.exit(1)

    # 5. Enforce minimum sample size
    if n_participants < MIN_PARTICIPANTS:
        logger.error(f"Sample size N={n_participants} < {MIN_PARTICIPANTS}. Study invalid.")
        write_validation_report(n_participants, variables, "FAILED_N_COUNT", logger)
        sys.exit(1)

    # 6. Save dataset (already on disk)
    save_dataset_to_disk(data_path, logger)

    # 7. Create manifest
    manifest = create_manifest(data_path, n_participants, variables, logger)

    # 8. Write manifest atomically
    try:
        write_manifest_atomically(manifest, MANIFEST_PATH, logger)
    except Exception as e:
        logger.error(f"Failed to write manifest: {e}")
        sys.exit(1)

    # 9. Write validation report
    write_validation_report(n_participants, variables, "SUCCESS", logger)

    logger.info("Download and validation completed successfully.")
    print(f"SUCCESS: Dataset downloaded. N={n_participants}. Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
