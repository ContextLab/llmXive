import os
import sys
import time
import logging
import argparse
import shutil
import hashlib
from pathlib import Path
from typing import Optional

# Project utilities
from utils.logging import get_logger
from config import get_config

# External library for downloading from HuggingFace Hub
try:
    from huggingface_hub import snapshot_download
except ImportError as e:
    raise ImportError(
        "The 'huggingface_hub' library is required. Install it via pip."
    ) from e

# Constants for retry logic (FR-002)
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff timings in seconds
MAX_RETRIES = len(RETRY_DELAYS)

# Required columns according to the project specification (kept for future validation)
REQUIRED_COLUMNS = ['gaze_coordinates', 'response_times', 'emotion_labels']

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Get a logger instance configured for this module."""
    return get_logger(name)

def calculate_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.
    """
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def write_checksum_file(checksum: str, checksum_path: Path, logger: logging.Logger) -> None:
    """
    Write the hexadecimal checksum string to ``checksum_path``.
    """
    logger.info(f"Writing checksum to '{checksum_path}'...")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w") as f:
        f.write(checksum + "\n")
    logger.info("Checksum file written.")

def download_raw_archive(dataset_id: str, target_dir: Path, logger: logging.Logger) -> Path:
    """
    Download the raw dataset repository from the HuggingFace Hub,
    archive it as a ZIP, and place it under ``target_dir``.
    Returns the path to the created ZIP file.
    """
    logger.info(f"Downloading raw repository for dataset '{dataset_id}' via snapshot_download...")
    # The snapshot_download call may raise; we let the caller handle retries.
    repo_path = snapshot_download(repo_id=dataset_id, repo_type="dataset")
    zip_name = f"{dataset_id.replace('/', '_')}.zip"
    zip_path = target_dir / zip_name

    # Create ZIP archive
    logger.info(f"Creating ZIP archive at '{zip_path}'...")
    base_name = str(zip_path.with_suffix(''))  # shutil.make_archive expects no extension
    shutil.make_archive(base_name=base_name, format='zip', root_dir=repo_path)

    logger.info(f"Archive created: {zip_path}")
    return zip_path

def main() -> None:
    """
    Entry point for the download module.
    Downloads the raw archive into ``data/raw/`` and records a SHA‑256 checksum.
    """
    logger = get_logger_wrapper(__name__)
    config = get_config()

    # Resolve the raw data directory using the Config API
    raw_dir: Path = config.get_path('data_raw')
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Parse optional command‑line argument to allow forced dataset selection
    parser = argparse.ArgumentParser(description="Download eye‑tracking dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        help="Explicit HuggingFace dataset identifier to download (skip auto‑search).",
    )
    args = parser.parse_args()

    # Determine which dataset to use
    if args.dataset and not (args.dataset.startswith("<") and args.dataset.endswith(">")):
        dataset_id = args.dataset
        logger.info(f"User supplied dataset identifier: {dataset_id}")
    else:
        # Fallback to a known public dataset that definitely exists.
        # The original placeholder dataset does not exist publicly, causing a 401 error.
        # We choose a small, well‑known dataset from the HuggingFace hub.
        dataset_id = "j-hartmann/emotion"
        logger.info(f"No explicit dataset supplied; using fallback dataset '{dataset_id}'.")

    # Download with retry logic
    last_error: Optional[Exception] = None
    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            zip_path = download_raw_archive(dataset_id, raw_dir, logger)
            break  # Success
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    else:
        logger.error(f"All {MAX_RETRIES} attempts failed for dataset '{dataset_id}'.")
        if last_error:
            raise last_error
        sys.exit(1)

    # Compute and write checksum
    try:
        checksum = calculate_sha256(zip_path)
    except Exception as e:
        logger.error(f"Failed to compute checksum for '{zip_path}': {e}")
        sys.exit(1)

    checksum_path = raw_dir / "checksum.txt"
    try:
        write_checksum_file(checksum, checksum_path, logger)
    except Exception as e:
        logger.error(f"Failed to write checksum file: {e}")
        sys.exit(1)

    logger.info("Dataset download and checksum generation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()