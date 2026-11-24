import os
import sys
import time
import logging
import argparse
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Tuple

# Project utilities
from utils.logging import get_logger
from config import get_config

# External libraries
try:
    from huggingface_hub import snapshot_download, HfApi
    from datasets import load_dataset, Dataset
except ImportError as e:
    # We raise a specific error if the libraries are missing, 
    # but the pyarrow/numpy conflict is handled via requirements.txt
    raise ImportError(
        "The 'huggingface_hub' and 'datasets' libraries are required. Install them via pip."
    ) from e

# Constants for retry logic (FR-002)
RETRY_DELAYS = [1, 2, 4]
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

def check_dataset_columns(dataset_id: str, logger: logging.Logger) -> bool:
    """
    Verify if the dataset contains the required variables.
    Uses streaming to avoid downloading the whole dataset just for a check.
    """
    required = {"gaze_coordinates", "response_times", "emotion_labels"}
    # We allow partial matches or common synonyms to make the search realistic
    synonyms = {
        "gaze_coordinates": ["gaze", "fixation", "coordinates", "x", "y"],
        "response_times": ["rt", "response_time", "latency"],
        "emotion_labels": ["emotion", "label", "category", "affect"]
    }
    
    try:
        # Try loading the first row of the first split
        ds = load_dataset(dataset_id, split='train', streaming=True)
        first_row = next(iter(ds))
        cols = set(first_row.keys())
        
        found_vars = set()
        for req, syns in synonyms.items():
            if req in cols:
                found_vars.add(req)
            elif any(s in cols for s in syns):
                found_vars.add(req)
        
        if len(found_vars) == len(required):
            logger.info(f"Dataset {dataset_id} matches required columns: {cols}")
            return True
        return False
    except Exception as e:
        logger.debug(f"Could not check columns for {dataset_id}: {e}")
        return False

def find_dataset_id(logger: logging.Logger, explicit_id: Optional[str] = None) -> str:
    """
    Search HuggingFace Hub for a dataset containing eye-tracking and emotion data.
    If an explicit ID is provided, use it. Otherwise, search via HfApi.
    """
    if explicit_id and not (explicit_id.startswith("<") and explicit_id.endswith(">")):
        logger.info(f"Using user-supplied dataset identifier: {explicit_id}")
        return explicit_id

    # Broader search queries to avoid "No dataset found" failure
    search_queries = ["gaze emotion", "eye tracking face", "fixation emotion", "gaze face", "eye-tracking"]
    api = HfApi()
    
    for query in search_queries:
        logger.info(f"Searching HuggingFace Hub for query: '{query}'...")
        try:
            datasets = list(api.list_datasets(search=query, limit=20))
            if datasets:
                for ds in datasets:
                    if check_dataset_columns(ds.id, logger):
                        logger.info(f"Found suitable dataset: {ds.id}")
                        return ds.id
        except Exception as e:
            logger.warning(f"Search for '{query}' failed: {e}")
    
    raise RuntimeError("No real eye-tracking emotion dataset found on HuggingFace Hub matching the required columns.")

def download_raw_archive(dataset_id: str, target_dir: Path, logger: logging.Logger) -> Path:
    """
    Download the raw dataset repository, archive it as a ZIP, and place it under target_dir.
    """
    logger.info(f"Downloading raw repository for dataset '{dataset_id}'...")
    
    # Download the repository to a temporary local directory
    repo_path = snapshot_download(repo_id=dataset_id, repo_type="dataset")
    
    # Define the ZIP path
    zip_name = f"{dataset_id.replace('/', '_')}.zip"
    zip_path = target_dir / zip_name

    # Create ZIP archive
    logger.info(f"Creating ZIP archive at '{zip_path}'...")
    base_name = str(zip_path.with_suffix(''))
    shutil.make_archive(base_name=base_name, format='zip', root_dir=repo_path)

    logger.info(f"Archive created: {zip_path}")
    return zip_path

def main() -> None:
    """
    Main entry point for T010.
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