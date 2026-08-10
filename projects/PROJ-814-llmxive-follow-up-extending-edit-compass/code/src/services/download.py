import os
import sys
import hashlib
import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import logging utility from the project's existing structure
from src.utils.logging import get_logger, setup_logging

# Constants for the Edit-Compass dataset
HUGGINGFACE_REPO_ID = "llmXive/Edit-Compass"
DATASET_FILE_NAME = "edit_compass_metadata.json"
TARGET_CATEGORIES = ["World Knowledge Reasoning", "Visual Reasoning"]
RAW_DATA_DIR = Path("data/raw")

# Configure logging
logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate SHA256 for {file_path}: {e}")
        raise

def verify_download(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """Verify the downloaded file exists and optionally matches a checksum."""
    if not file_path.exists():
        logger.error(f"Downloaded file not found: {file_path}")
        return False
    
    if expected_checksum:
        actual_checksum = calculate_sha256(file_path)
        if actual_checksum != expected_checksum:
            logger.error(f"Checksum mismatch. Expected: {expected_checksum}, Got: {actual_checksum}")
            return False
    return True

def download_from_huggingface(repo_id: str, filename: str, output_dir: Path) -> Path:
    """
    Download a file from Hugging Face Hub using huggingface-cli or hf_hub_download.
    Falls back to wget if huggingface-cli is not available.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    if output_path.exists():
        logger.info(f"File already exists: {output_path}")
        return output_path

    try:
        # Attempt to use huggingface_hub library if available
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=output_dir,
            force_download=True
        )
        logger.info(f"Successfully downloaded via hf_hub_download: {downloaded_path}")
        return Path(downloaded_path)
    except ImportError:
        logger.warning("huggingface_hub not installed. Attempting wget/curl fallback.")
    except Exception as e:
        logger.warning(f"hf_hub_download failed: {e}. Attempting wget/curl fallback.")

    # Fallback: Construct URL and use wget/curl
    # Hugging Face file URL pattern: https://huggingface.co/{repo_id}/resolve/main/{filename}
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    try:
        # Try wget first
        subprocess.run(["wget", "-O", str(output_path), url], check=True)
        logger.info(f"Successfully downloaded via wget: {output_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Try curl as second fallback
            subprocess.run(["curl", "-L", "-o", str(output_path), url], check=True)
            logger.info(f"Successfully downloaded via curl: {output_path}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to download file using wget or curl: {e}")
            raise FileNotFoundError(f"Could not download {filename} from {url}")
    
    return output_path

def validate_dataset_structure(data_path: Path) -> Tuple[bool, str]:
    """
    Validate the downloaded dataset:
    1. Check if 'category' key exists in metadata records.
    2. Verify at least one record contains a target category.
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {e}"
    except Exception as e:
        return False, f"Failed to read file: {e}"

    if not isinstance(data, list):
        # If it's a dict with a key like 'data' or 'examples', try to extract the list
        if isinstance(data, dict):
            possible_keys = ['data', 'examples', 'records', 'items']
            extracted = None
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    extracted = data[key]
                    break
            if extracted is None:
                # Try to find any list value
                for key, value in data.items():
                    if isinstance(value, list):
                        extracted = value
                        break
            if extracted:
                data = extracted
            else:
                return False, "Dataset is neither a list nor a dict containing a list of records."
        else:
            return False, "Dataset must be a list of records or a dict containing one."

    if len(data) == 0:
        return False, "Dataset is empty."

    # Check for 'category' key in the first record
    first_record = data[0]
    if not isinstance(first_record, dict):
        return False, "First record is not a dictionary."

    if 'category' not in first_record:
        return False, "Missing 'category' key in dataset metadata."

    # Check for presence of target categories
    found_categories = set()
    for record in data:
        if isinstance(record, dict) and 'category' in record:
            cat = record['category']
            if cat in TARGET_CATEGORIES:
                found_categories.add(cat)
    
    if not found_categories:
        return False, f"No records found for target categories: {TARGET_CATEGORIES}"

    logger.info(f"Validation passed. Found categories: {found_categories}")
    return True, "Validation successful."

def main():
    """
    Main entry point for the download script.
    1. Downloads the Edit-Compass dataset.
    2. Validates the structure and content.
    3. Saves raw data to data/raw/.
    """
    setup_logging()
    
    logger.info("Starting Edit-Compass dataset download.")
    
    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = RAW_DATA_DIR / DATASET_FILE_NAME
    
    try:
        # Download
        logger.info(f"Downloading from Hugging Face: {HUGGINGFACE_REPO_ID}")
        downloaded_path = download_from_huggingface(HUGGINGFACE_REPO_ID, DATASET_FILE_NAME, RAW_DATA_DIR)
        
        if not verify_download(downloaded_path):
            logger.error("Download verification failed.")
            sys.exit(1)
        
        # Validate structure
        logger.info("Validating dataset structure and content.")
        is_valid, message = validate_dataset_structure(downloaded_path)
        
        if not is_valid:
            logger.error(f"ERROR: {message}")
            sys.exit(1)
        
        logger.info("Dataset download and validation completed successfully.")
        logger.info(f"Raw data saved to: {downloaded_path}")
        
    except FileNotFoundError as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()