import os
import sys
import hashlib
import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Configuration for the Edit-Compass dataset
HUGGINGFACE_REPO = "Edit-Compass/Dataset"
REVISION = "main"
TARGET_FILE = "edit_compass_metadata.json"  # Assumed metadata filename

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError as e:
        logger.error(f"File not found during hash calculation: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}") from e
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise PermissionError(f"Permission denied: {file_path}") from e

def verify_download(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """Verify the downloaded file exists and optionally matches hash."""
    if not file_path.exists():
        raise FileNotFoundError(f"Downloaded file not found: {file_path}")
    
    if expected_hash:
        actual_hash = calculate_sha256(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Hash mismatch. Expected: {expected_hash}, Got: {actual_hash}")
            return False
    return True

def download_from_huggingface(output_dir: Path, filename: str = TARGET_FILE) -> Path:
    """
    Download a file from Hugging Face Hub.
    Raises FileNotFoundError if the file is missing from the repo or local cache fails.
    """
    from huggingface_hub import hf_hub_download, HfFileSystem
    
    output_dir.mkdir(parents=True, exist_ok=True)
    local_path = output_dir / filename

    # Check if file exists in the remote repo first to fail loudly if missing
    fs = HfFileSystem()
    repo_path = f"{HUGGINGFACE_REPO}/{filename}"
    if not fs.exists(repo_path):
        raise FileNotFoundError(f"File '{filename}' not found in HuggingFace repo '{HUGGINGFACE_REPO}'")

    try:
        logger.info(f"Downloading {filename} from {HUGGINGFACE_REPO}...")
        # download_file handles caching; if it fails, it raises HFValidationError or similar
        downloaded_path = hf_hub_download(
            repo_id=HUGGINGFACE_REPO,
            filename=filename,
            revision=REVISION,
            local_dir=output_dir,
            local_dir_use_symlinks=False
        )
        return Path(downloaded_path)
    except Exception as e:
        # Map HF exceptions to FileNotFoundError for consistent handling in main
        if "404" in str(e) or "not found" in str(e).lower():
            raise FileNotFoundError(f"Failed to download {filename}: File not found on remote.") from e
        raise RuntimeError(f"Failed to download {filename}: {str(e)}") from e

def validate_dataset_structure(data_path: Path) -> bool:
    """
    Validate that the raw dataset has the expected structure (specifically 'category' key).
    Raises ValueError if structure is invalid.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in dataset file: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to read dataset file: {e}") from e

    if not isinstance(data, list):
        # If it's a dict with a specific key, adjust logic, but assuming list of records
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        else:
            raise ValueError("Dataset must be a list of records or a dict with 'data' key")

    if len(data) == 0:
        logger.warning("Dataset is empty.")
        return False

    # Check for required keys in at least one record
    required_keys = {'category', 'source_image_path', 'edited_image_path', 'instruction'}
    sample_record = data[0]
    
    if not isinstance(sample_record, dict):
        raise ValueError("Dataset records must be dictionaries")

    missing_keys = required_keys - set(sample_record.keys())
    if missing_keys:
        raise ValueError(f"Dataset records missing required keys: {missing_keys}")

    # Verify presence of target categories
    target_categories = {"World Knowledge Reasoning", "Visual Reasoning"}
    found_categories = set()
    for record in data:
        if isinstance(record, dict) and 'category' in record:
            found_categories.add(record['category'])
    
    if not found_categories.intersection(target_categories):
        raise ValueError(
            f"ERROR: No records found for target categories: {target_categories}. "
            f"Found categories: {found_categories}"
        )

    logger.info("Dataset structure validation passed.")
    return True

def main():
    setup_logging()
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting dataset download and validation...")

    try:
        # 1. Download
        file_path = download_from_huggingface(raw_dir)
        logger.info(f"Downloaded file to: {file_path}")

        # 2. Verify (if checksums were tracked, otherwise just existence)
        # For now, we rely on the download success and structure validation
        if not verify_download(file_path):
            logger.error("Download verification failed.")
            sys.exit(1)

        # 3. Validate Structure
        if not validate_dataset_structure(file_path):
            logger.error("Dataset validation failed.")
            sys.exit(1)

        logger.info("Download and validation successful.")

    except FileNotFoundError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
