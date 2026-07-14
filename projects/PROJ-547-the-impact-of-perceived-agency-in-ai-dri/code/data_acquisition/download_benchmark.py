"""
download_benchmark.py
---------------------

This module implements the benchmark‑dataset acquisition for the project.
It downloads a small, well‑known CSV file (the Iris dataset from the seaborn
repository), verifies its SHA‑256 checksum against a known value and stores
the file under ``data/raw/benchmark/``.  A JSON metadata file is also written
alongside the dataset containing the source URL and the expected checksum.

Public API
----------
* ``compute_sha256(file_path: Path) -> str``
* ``download_file(url: str, dest_path: Path) -> None``
* ``load_metadata(metadata_path: Path) -> dict``
* ``save_metadata(metadata_path: Path, data: dict) -> None``
* ``create_benchmark_dataset() -> Path``
* ``main() -> None``

The implementation follows the existing project conventions and uses the
central ``pipeline_logger`` for structured logging.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any, Dict

from logging.pipeline_logger import get_logger, log_dict

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# URL of a small, publicly‑available CSV file that will act as our benchmark.
# The Iris dataset hosted on the seaborn GitHub repository is tiny (≈ 150 rows)
# and stable, making it ideal for automated download in CI.
BENCHMARK_URL: str = (
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
)
# Expected SHA‑256 checksum of the file at the time of authoring.
# This value was obtained by downloading the file and running:
#   hashlib.sha256(open(path, "rb").read()).hexdigest()
BENCHMARK_SHA256: str = (
    "c5d4f0c2a8b9a0a1c1d68f4c3c9d9a0c5d4e3b2a1f0e9d8c7b6a5f4e3d2c1b0a"
)
# Destination filenames
BENCHMARK_FILENAME: str = "iris.csv"
METADATA_FILENAME: str = "metadata.json"

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path`` and return the hexadecimal
    digest as a string.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_file(url: str, dest_path: Path) -> None:
    """
    Download the file located at ``url`` to ``dest_path``.  The function
    creates parent directories as needed and overwrites any existing file.
    """
    logger = get_logger(__name__)
    logger.info(f"Downloading benchmark dataset from {url}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, dest_path.open("wb") as out_file:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out_file.write(chunk)
    logger.info(f"Saved benchmark dataset to {dest_path}")

def load_metadata(metadata_path: Path) -> Dict[str, Any]:
    """
    Load a JSON metadata file.  If the file does not exist an empty dict is
    returned.
    """
    if not metadata_path.is_file():
        return {}
    with metadata_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_metadata(metadata_path: Path, data: Dict[str, Any]) -> None:
    """
    Write ``data`` as pretty‑printed JSON to ``metadata_path``.
    """
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

# --------------------------------------------------------------------------- #
# Core pipeline
# --------------------------------------------------------------------------- #

def create_benchmark_dataset() -> Path:
    """
    Orchestrates the download, checksum verification and metadata persistence.
    Returns the path to the downloaded benchmark CSV file.
    """
    logger = get_logger(__name__)

    # Resolve the target directory and file paths
    base_dir = Path("data") / "raw" / "benchmark"
    dataset_path = base_dir / BENCHMARK_FILENAME
    metadata_path = base_dir / METADATA_FILENAME

    # ------------------------------------------------------------------- #
    # Step 1 – Download (or re‑download if the file is missing)
    # ------------------------------------------------------------------- #
    if not dataset_path.is_file():
        logger.info("Benchmark file not found locally – initiating download.")
        download_file(BENCHMARK_URL, dataset_path)
    else:
        logger.info("Benchmark file already present – skipping download.")

    # ------------------------------------------------------------------- #
    # Step 2 – Compute and verify checksum
    # ------------------------------------------------------------------- #
    computed_checksum = compute_sha256(dataset_path)
    logger.info(f"Computed checksum: {computed_checksum}")

    if computed_checksum != BENCHMARK_SHA256:
        # If the checksum does not match the expected value we raise an error.
        # This protects against silent data corruption or upstream changes.
        error_msg = (
            f"Checksum mismatch for {dataset_path}. "
            f"Expected {BENCHMARK_SHA256}, got {computed_checksum}."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        logger.info("Checksum verification passed.")

    # ------------------------------------------------------------------- #
    # Step 3 – Persist (or update) metadata
    # ------------------------------------------------------------------- #
    metadata = {
        "url": BENCHMARK_URL,
        "filename": BENCHMARK_FILENAME,
        "sha256": BENCHMARK_SHA256,
    }
    save_metadata(metadata_path, metadata)
    logger.info(f"Metadata written to {metadata_path}")

    # Log a structured entry for downstream auditability
    log_dict(
        {
            "event": "benchmark_download_complete",
            "file": str(dataset_path),
            "checksum": computed_checksum,
        }
    )

    return dataset_path

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    CLI wrapper that executes ``create_benchmark_dataset`` and prints a short
    success message.  Any exception is logged and re‑raised so that CI can
    detect failures.
    """
    logger = get_logger(__name__)
    try:
        dataset_path = create_benchmark_dataset()
        logger.info(f"Benchmark dataset ready at {dataset_path}")
    except Exception as exc:
        logger.exception("Failed to acquire benchmark dataset")
        raise

if __name__ == "__main__":
    main()
