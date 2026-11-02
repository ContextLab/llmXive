import os
import sys
import time
import logging
import argparse
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List

# Project utilities
from utils.logging import get_logger
from config import get_config

# External library for downloading from HuggingFace Hub
try:
    from huggingface_hub import snapshot_download, HfApi
except ImportError as e:
    raise ImportError(
        "The 'huggingface_hub' library is required. Install it via pip."
    ) from e

# Constants for retry logic (FR-002)
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff timings in seconds
MAX_RETRIES = len(RETRY_DELAYS)

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Get a logger instance configured for this module."""
    return get_logger(name)

def calculate_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def write_checksum_file(checksum: str, checksum_path: Path, logger: logging.Logger) -> None:
    """Write the hexadecimal checksum string to checksum_path."""
    logger.info(f"Writing checksum to '{checksum_path}'...")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w") as f:
        f.write(checksum + "\n")
    logger.info("Checksum file written.")

def find_dataset_id(logger: logging.Logger, explicit_id: Optional[str] = None) -> str:
    """
    Search HuggingFace Hub for a dataset containing eye-tracking and emotion data.
    If an explicit ID is provided, use it. Otherwise, search via HfApi.
    """
    if explicit_id and not (explicit_id.startswith("<") and explicit_id.endswith(">")):
        logger.info(f"Using user-supplied dataset identifier: {explicit_id}")
        return explicit_id

    search_queries = ["eye tracking emotion", "gaze emotion", "eye tracking face"]
    api = HfApi()
    
    for query in search_queries:
        logger.info(f"Searching HuggingFace Hub for query: '{query}'...")
        try:
            datasets = list(api.list_datasets(search=query, limit=5))
            if datasets:
                dataset_id = datasets[0].id
                logger.info(f"Found suitable dataset: {dataset_id}")
                return dataset_id
        except Exception as e:
            logger.warning(f"Search for '{query}' failed: {e}")
    
    # Final fallback to a known real dataset if search fails, 
    # but we must ensure it's a valid repo ID.
    # 'iris' is a common small dataset, but for this research, we need something more specific.
    # If we reach here and have no results, we fail as per "Real data only" constraint.
    raise RuntimeError("No real eye-tracking emotion dataset found on HuggingFace Hub via search.")

def download_raw_archive(dataset_id: str, target_dir: Path, logger: logging.Logger) -> Path:
    """
    Download the raw dataset repository from the HuggingFace Hub,
    archive it as a ZIP, and place it under target_dir.
    """
    logger.info(f"Downloading raw repository for dataset '{dataset_id}' via snapshot_download...")
    
    # Download the repository to a temporary local directory
    repo_path = snapshot_download(repo_id=dataset_id, repo_type="dataset")
    
    # Define the ZIP path
    zip_name = f"{dataset_id.replace('/', '_')}.zip"
    zip_path = target_dir / zip_name

    # Create ZIP archive of the downloaded repository
    logger.info(f"Creating ZIP archive at '{zip_path}'...")
    # shutil.make_archive expects base_name without extension
    base_name = str(zip_path.with_suffix(''))
    shutil.make_archive(base_name=base_name, format='zip', root_dir=repo_path)

    logger.info(f"Archive created: {zip_path}")
    return zip_path

def main() -> None:
    """
    Entry point for the download module.
    Downloads the raw archive into data/raw/ and records a SHA-256 checksum.
    """
    logger = get_logger_wrapper(__name__)
    config = get_config()

    # Resolve the raw data directory
    raw_dir: Path = config.get_path('data_raw')
    raw_dir.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Download eye-tracking dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        help="Explicit HuggingFace dataset identifier to download.",
    )
    args = parser.parse_args()

    try:
        dataset_id = find_dataset_id(logger, args.dataset)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # Download with retry logic (FR-002)
    last_error: Optional[Exception] = None
    zip_path: Optional[Path] = None
    
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
    if zip_path:
        try:
            checksum = calculate_sha256(zip_path)
            checksum_path = raw_dir / "checksum.txt"
            write_checksum_file(checksum, checksum_path, logger)
        except Exception as e:
            logger.error(f"Failed to compute or write checksum for '{zip_path}': {e}")
            sys.exit(1)

    logger.info("Dataset download and checksum generation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()