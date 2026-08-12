"""
Download and validation service for the Edit-Compass dataset.
Implements strict 'Fail-Loud' logic: no synthetic fallbacks allowed.
"""

import os
import sys
import hashlib
import logging
import subprocess
import json
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Custom Exception for Data Fetch Failures
class DataFetchError(Exception):
    """Raised when a real data fetch fails and no synthetic fallback is permitted."""
    def __init__(self, message: str, error_code: int = 1):
        super().__init__(message)
        self.error_code = error_code

# Configuration
DATASET_URL = "https://huggingface.co/datasets/HuggingFaceH4/edit-compass"
# Note: Direct file URL might vary. We attempt to fetch the main JSON file.
# Based on typical HF structure, we target the data file if available via direct link
# or use a git clone/wget strategy. For this implementation, we assume a direct JSON
# download path or a known file within the repo structure.
# If the dataset is a folder, we might need to list files.
# For robustness, we will attempt to download the specific file if the URL is direct,
# or clone the repo if it's a directory.
# Given the task description: "fetch Edit-Compass dataset via wget/curl from official repo"
# We will target a specific file path if known, or the root if it's a single file repo.
# Assuming the file is named 'edit-compass.json' in the repo root for this exercise.
# If the repo is a dataset card, we might need to use the 'data' branch or specific file.
# Let's assume the direct link to the JSON file is available or we clone.
# To be safe and "Fail Loud", we will try to wget a specific expected file.
# If the dataset is large and not a single file, we might need to clone.
# For this task, we assume the file `data/edit-compass.json` exists in the repo.
# We will use the raw content URL if possible, or clone.

# Using a generic approach:
# 1. Check if URL is a direct file link.
# 2. If not, we might need to clone.
# However, the task says "wget/curl". We will attempt to download a specific file.
# If the dataset is on HuggingFace, the raw file URL is usually:
# https://huggingface.co/datasets/{repo_id}/resolve/{branch}/{path}
# We will assume the file is at the root or a known path.
# Let's define the target file name and a potential raw URL.

RAW_DATA_PATH = Path("data/raw")
OUTPUT_FILE = RAW_DATA_PATH / "edit-compass.json"
TARGET_CATEGORY_1 = "World Knowledge Reasoning"
TARGET_CATEGORY_2 = "Visual Reasoning"

logger = logging.getLogger(__name__)

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_download(filepath: Path, expected_hash: Optional[str] = None) -> bool:
    """Verify file exists and optionally matches hash."""
    if not filepath.exists():
        return False
    if expected_hash:
        actual_hash = calculate_sha256(filepath)
        return actual_hash == expected_hash
    return True

def download_from_huggingface(url: str, output_path: Path) -> None:
    """
    Download dataset using wget/curl.
    FAILS LOUDLY: Raises DataFetchError if download fails.
    NO synthetic fallback.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Attempting to download from: {url}")
    logger.info(f"Target path: {output_path}")

    # Try wget first
    try:
        # Using --show-progress and --timeout for robustness
        cmd = ["wget", "--timeout=60", "--tries=3", "-O", str(output_path), url]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Download successful via wget.")
        return
    except subprocess.CalledProcessError as e:
        logger.warning(f"Wget failed: {e.stderr}")
        # Fall back to curl
        try:
            cmd = ["curl", "-L", "--connect-timeout", "30", "--max-time", "120", "-o", str(output_path), url]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Download successful via curl.")
            return
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl also failed: {e.stderr}")
            raise DataFetchError(
                "FATAL: Real data fetch failed. Aborting. Do not substitute synthetic data.",
                error_code=1
            )
    except FileNotFoundError:
        raise DataFetchError(
            "FATAL: Real data fetch failed. Aborting. Do not substitute synthetic data.",
            error_code=1
        )

def validate_dataset_structure(filepath: Path) -> bool:
    """
    Validate the downloaded file structure.
    Checks for 'category' key and presence of target categories.
    FAILS LOUDLY: Raises DataFetchError if structure is invalid.
    """
    if not filepath.exists():
        raise DataFetchError(
            "FATAL: Downloaded file does not exist. Aborting.",
            error_code=1
        )

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataFetchError(
            f"FATAL: Invalid JSON structure in downloaded file. Aborting. Error: {e}",
            error_code=1
        )

    if not isinstance(data, list):
        raise DataFetchError(
            "FATAL: Expected dataset to be a JSON list. Aborting.",
            error_code=1
        )

    if len(data) == 0:
        raise DataFetchError(
            "FATAL: Dataset is empty. Aborting.",
            error_code=1
        )

    # Check first record for 'category' key
    first_record = data[0]
    if 'category' not in first_record:
        raise DataFetchError(
            "FATAL: Missing 'category' key in dataset records. Structure mismatch. Aborting.",
            error_code=1
        )

    # Verify at least one record contains target categories
    found_target = False
    for record in data:
        cat = record.get('category', '')
        if cat in [TARGET_CATEGORY_1, TARGET_CATEGORY_2]:
            found_target = True
            break

    if not found_target:
        # This is a specific case mentioned in T011: "If zero records match target categories, log WARNING and exit 0"
        # However, T035 is about "Fail-Loud" on fetch/structure.
        # The task T011 says: "If zero records match target categories, log WARNING... and exit 0".
        # But T035 says: "If wget/curl fails or the file structure is invalid, raise DataFetchError".
        # Missing target categories is a data content issue, not necessarily a fetch/structure failure.
        # T011 logic: "If keys are missing, exit with code 1... If zero records match target categories, log WARNING... exit 0".
        # We will follow T011's content validation logic here, but ensure fetch failures are loud.
        logger.warning("WARNING: No records found for target categories in the downloaded dataset.")
        # We do NOT raise DataFetchError here, as the data was fetched successfully and structure is valid (has 'category').
        # It's just that the content doesn't match our filter.
        return False 

    return True

def main():
    """Main entry point for download stage."""
    # Setup logging if not already done
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Determine URL
        # The task specifies: https://huggingface.co/datasets/HuggingFaceH4/edit-compass
        # This is a repo URL. We need a direct file link.
        # Often datasets have a 'data' directory or a specific file.
        # Since we cannot browse the repo dynamically here, we assume a standard path
        # or try to clone if wget fails on the repo URL.
        # However, wget on a repo URL usually fails.
        # Let's try to construct a likely raw file URL or use git clone if wget fails.
        
        # Attempt 1: Direct download of a likely file
        # Many HF datasets have a 'data.json' or similar.
        # If the dataset is 'edit-compass', maybe the file is 'edit-compass.json'?
        # We will try the URL provided in the task as a base, but we need a file.
        # Let's assume the file is at the root of the dataset repo if it's a single file repo.
        # If not, we might need to use `huggingface-cli` or `wget` on the raw link.
        # Since we can't guarantee the raw link without browsing, we will try to wget the repo URL
        # which might redirect to a landing page (not a file).
        # Better approach for "Fail Loud" and robustness:
        # Try to wget the raw file if we can guess it, or use git clone.
        # Given the constraints, let's assume the file is accessible via a direct link
        # or we clone the repo to data/raw and then process.
        
        # Let's try to download the file from the raw content URL if possible.
        # If the dataset is at HuggingFaceH4/edit-compass, the raw file might be:
        # https://huggingface.co/datasets/HuggingFaceH4/edit-compass/resolve/main/data.json
        # Or similar.
        
        # Since we cannot know the exact filename without external knowledge,
        # and the task says "fetch... from official repo", we will try to clone the repo
        # if direct download fails, as that is a valid "fetch" method.
        # But the task says "wget/curl".
        
        # Let's try a common pattern:
        possible_files = [
            "https://huggingface.co/datasets/HuggingFaceH4/edit-compass/resolve/main/edit-compass.json",
            "https://huggingface.co/datasets/HuggingFaceH4/edit-compass/resolve/main/data.json",
            "https://huggingface.co/datasets/HuggingFaceH4/edit-compass/resolve/main/data/train.json"
        ]
        
        downloaded = False
        for url in possible_files:
            try:
                download_from_huggingface(url, OUTPUT_FILE)
                downloaded = True
                break
            except DataFetchError:
                continue

        if not downloaded:
            raise DataFetchError(
                "FATAL: Could not fetch any known data file from HuggingFace. Aborting.",
                error_code=1
            )

        # Validate structure
        if not validate_dataset_structure(OUTPUT_FILE):
            # If no target categories found, we log warning and exit 0 (per T011)
            # But we must ensure the data is REAL.
            logger.warning("WARNING: No records found for target categories. Exiting 0.")
            sys.exit(0)

        logger.info("Download and validation successful.")
        sys.exit(0)

    except DataFetchError as e:
        logger.critical(str(e))
        sys.exit(e.error_code)
    except Exception as e:
        logger.critical(f"FATAL: Unexpected error during download: {e}. Aborting.")
        sys.exit(1)

if __name__ == "__main__":
    main()