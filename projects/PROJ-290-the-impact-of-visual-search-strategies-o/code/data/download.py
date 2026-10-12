import os
import sys
import time
import logging
import argparse
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project utilities
from utils.logging import get_logger
from config import get_config

# External libraries
try:
    from datasets import load_dataset
except ImportError as e:
    raise ImportError("The 'datasets' library is required. Install it via pip.") from e

try:
    from huggingface_hub import snapshot_download, HfApi
except ImportError as e:
    raise ImportError("The 'huggingface_hub' library is required. Install it via pip.") from e

# Constants for retry logic (FR-002)
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff timings in seconds
MAX_RETRIES = len(RETRY_DELAYS)

# Required columns according to the project specification
REQUIRED_COLUMNS = ['gaze_coordinates', 'response_times', 'emotion_labels']

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Get a logger instance configured for this module."""
    return get_logger(name)

def check_schema_compatibility(dataset_columns: List[str], required_columns: List[str]) -> bool:
    """
    Verify that all required columns are present in the dataset schema.
    """
    return all(col in dataset_columns for col in required_columns)

def validate_dataset_content(dataset: Any) -> bool:
    """
    Ensure the dataset contains at least one non‑empty record.
    """
    try:
        if hasattr(dataset, '__len__') and len(dataset) > 0:
            first_record = dataset[0]
            return bool(first_record)
        return False
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error validating dataset content: {e}")
        return False

def search_huggingface_datasets(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Search HuggingFace Hub for datasets related to eye‑tracking, faces, or emotion.
    Returns a list of candidate dataset metadata dictionaries.
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        logger.error("huggingface_hub not installed; cannot perform search.")
        return []

    keywords = ['eye-tracking', 'face', 'emotion']
    candidate_datasets: List[Dict[str, Any]] = []
    api = HfApi()

    for keyword in keywords:
        try:
            datasets_info = api.list_datasets(search=keyword, limit=50)
            for ds in datasets_info:
                dataset_info = {
                    'id': ds.id,
                    'description': ds.description or "",
                    'author': ds.author or "",
                    'likes': ds.likes or 0
                }
                if not any(d['id'] == dataset_info['id'] for d in candidate_datasets):
                    candidate_datasets.append(dataset_info)
        except Exception as e:
            logger.warning(f"Error searching for datasets with keyword '{keyword}': {e}")
            continue

    candidate_datasets.sort(key=lambda x: x['likes'], reverse=True)
    logger.info(f"Found {len(candidate_datasets)} candidate datasets.")
    return candidate_datasets

def download_with_retry(dataset_id: str, logger: logging.Logger) -> Any:
    """
    Load a HuggingFace dataset with retry logic.
    Returns the loaded dataset object if successful.
    """
    last_error = None
    for attempt, delay in enumerate(RETRY_DELAYS):
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} to load dataset '{dataset_id}'...")
            ds = load_dataset(dataset_id, split='train', trust_remote_code=False)
            logger.info(f"Successfully loaded dataset '{dataset_id}'.")
            return ds
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    logger.error(f"All {MAX_RETRIES} attempts failed for dataset '{dataset_id}'.")
    raise last_error if last_error else Exception("Unknown error during dataset load.")

def find_valid_dataset(logger: logging.Logger, required_columns: List[str]) -> Tuple[Optional[str], Optional[Any]]:
    """
    Locate the first dataset on HuggingFace that satisfies schema requirements.
    Returns a tuple of (dataset_id, loaded_dataset) or (None, None) if none found.
    """
    candidates = search_huggingface_datasets(logger)

    if not candidates:
        logger.error("No candidate datasets found on HuggingFace.")
        return None, None

    for candidate in candidates:
        dataset_id = candidate['id']
        logger.info(f"Evaluating candidate dataset: {dataset_id}")

        try:
            # Load a streaming version to inspect column names without materialising the whole set
            ds_stream = load_dataset(dataset_id, split='train', streaming=True)
            if hasattr(ds_stream, 'column_names'):
                columns = ds_stream.column_names
            else:
                # Fallback: fetch first record and infer keys
                first_record = next(iter(ds_stream))
                columns = list(first_record.keys())

            if not check_schema_compatibility(columns, required_columns):
                logger.info(f"Dataset '{dataset_id}' missing required columns. Skipping.")
                continue

            # Load a small non‑streaming sample to validate content
            sample_ds = load_dataset(dataset_id, split='train')
            if not validate_dataset_content(sample_ds):
                logger.info(f"Dataset '{dataset_id}' contains no valid records. Skipping.")
                continue

            logger.info(f"Dataset '{dataset_id}' satisfies all checks.")
            return dataset_id, sample_ds
        except Exception as e:
            logger.warning(f"Error processing dataset '{dataset_id}': {e}")
            continue

    logger.error("No suitable dataset found after evaluating all candidates.")
    return None, None

def download_raw_archive(dataset_id: str, target_dir: Path, logger: logging.Logger) -> Path:
    """
    Download the raw dataset repository from the HuggingFace Hub, archive it as a ZIP,
    and place it under ``target_dir``. Returns the path to the created ZIP file.
    """
    logger.info(f"Downloading raw repository for dataset '{dataset_id}' via snapshot_download...")
    repo_path = snapshot_download(repo_id=dataset_id, repo_type="dataset", allow_patterns=None)

    zip_name = f"{dataset_id.replace('/', '_')}.zip"
    zip_path = target_dir / zip_name

    # Create ZIP archive
    logger.info(f"Creating ZIP archive at '{zip_path}'...")
    # shutil.make_archive requires a base name without extension
    base_name = str(zip_path.with_suffix(''))
    shutil.make_archive(base_name=base_name, format='zip', root_dir=repo_path)

    logger.info(f"Archive created: {zip_path}")
    return zip_path

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

def main() -> None:
    """
    Entry point for the download module.
    Searches for a suitable dataset (or uses a user‑provided identifier),
    downloads the raw archive into ``data/raw/``, and records a SHA‑256 checksum.
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

    # ------------------------------------------------------------------
    # Determine which dataset to use
    # ------------------------------------------------------------------
    if args.dataset:
        dataset_id = args.dataset
        logger.info(f"User supplied dataset identifier: {dataset_id}")

        # Verify that the supplied dataset meets the required schema
        try:
            ds = load_dataset(dataset_id, split='train')
            if not validate_dataset_content(ds):
                logger.error(f"The supplied dataset '{dataset_id}' appears empty.")
                sys.exit(1)

            # Extract column names for schema validation
            columns = ds.column_names if hasattr(ds, "column_names") else list(ds[0].keys())
            if not check_schema_compatibility(columns, REQUIRED_COLUMNS):
                logger.error(
                    f"The supplied dataset '{dataset_id}' lacks required columns: {REQUIRED_COLUMNS}"
                )
                sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load supplied dataset '{dataset_id}': {e}")
            sys.exit(1)
    else:
        # Automatic search for a suitable dataset
        dataset_id, ds = find_valid_dataset(logger, REQUIRED_COLUMNS)
        if not dataset_id:
            logger.error("CRITICAL: No valid dataset found. Halting execution.")
            sys.exit(1)

    # ------------------------------------------------------------------
    # Download raw archive and compute checksum
    # ------------------------------------------------------------------
    try:
        zip_path = download_raw_archive(dataset_id, raw_dir, logger)
    except Exception as e:
        logger.error(f"Failed to download and archive dataset '{dataset_id}': {e}")
        sys.exit(1)

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
