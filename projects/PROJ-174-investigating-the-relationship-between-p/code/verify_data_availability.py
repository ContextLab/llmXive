"""
verify_data_availability.py

Parses the '# Verified datasets' block in plan.md to determine if valid
eye-tracking datasets are available. If no valid source is found, the script
halts with exit code 1. If valid sources exist, it downloads them to data/raw/.
"""
import os
import sys
import re
import json
import hashlib
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging for this script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PLAN_MD_PATH = Path("plan.md")
DATA_RAW_DIR = Path("data/raw")
META_SUFFIX = "_meta.json"
EYE_TRACKING_KEYWORDS = ["eye-tracking", "eyetracking", "pupil", "gaze"]
INVALID_CONTENT_TYPES = ["fMRI", "structural", "diffusion", "EEG", "MEG"]

def parse_verified_datasets_block(plan_path: Path) -> List[Dict[str, Any]]:
    """
    Parses the '# Verified datasets' block from plan.md.
    
    Returns a list of dictionaries containing dataset metadata (id, url, type).
    Returns an empty list if the block is not found or empty.
    """
    if not plan_path.exists():
        logger.error(f"Plan file not found: {plan_path}")
        return []

    with open(plan_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find the block starting with '# Verified datasets'
    # and capturing everything until the next top-level header or end of file
    pattern = r'#\s*Verified datasets\s*\n(.*?)(?=\n#|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if not match:
        logger.warning("No '# Verified datasets' block found in plan.md")
        return []

    block_content = match.group(1).strip()
    
    if not block_content:
        logger.warning("The '# Verified datasets' block is empty.")
        return []

    datasets = []
    lines = block_content.split('\n')
    
    current_entry = {}
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Parse key-value pairs (e.g., "- ID: ds000001")
        if line.startswith('-'):
            # If we have a pending entry, save it
            if current_entry and current_entry.get('id'):
                datasets.append(current_entry)
            current_entry = {}
            line = line[1:].strip()
        
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            current_entry[key] = value

    # Append the last entry
    if current_entry and current_entry.get('id'):
        datasets.append(current_entry)

    return datasets

def is_valid_eye_tracking_dataset(dataset_info: Dict[str, Any]) -> bool:
    """
    Checks if a dataset entry represents a valid eye-tracking source.
    
    Criteria:
    1. Must contain eye-tracking related keywords in type or description.
    2. Must NOT be an fMRI or other non-eye-tracking modality.
    """
    if not dataset_info:
        return False

    # Check for invalid content types
    desc = (dataset_info.get('type', '') + ' ' + dataset_info.get('description', '')).lower()
    for invalid in INVALID_CONTENT_TYPES:
        if invalid.lower() in desc:
            logger.info(f"Rejecting dataset {dataset_info.get('id')}: contains invalid content type '{invalid}'")
            return False

    # Check for valid eye-tracking indicators
    is_eye_tracking = False
    for keyword in EYE_TRACKING_KEYWORDS:
        if keyword in desc:
            is_eye_tracking = True
            break
    
    # If no explicit keyword found but it has a URL and ID, we might need to verify further
    # For now, we rely on the plan.md content description.
    if not is_eye_tracking:
        logger.info(f"Rejecting dataset {dataset_info.get('id')}: no eye-tracking keywords found")
        return False

    return True

def hash_file(file_path: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        return ""

def write_meta(file_path: Path, meta_dict: Dict[str, Any]) -> None:
    """Writes metadata JSON file alongside the data file."""
    meta_path = file_path.with_suffix(file_path.suffix + META_SUFFIX)
    meta_dict['timestamp'] = str(Path(file_path).stat().st_mtime) # Simplified timestamp
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta_dict, f, indent=2)
    logger.info(f"Wrote metadata to {meta_path}")

def download_dataset(dataset_info: Dict[str, Any], target_dir: Path) -> bool:
    """
    Downloads a dataset from a URL to the target directory.
    Returns True on success, False on failure.
    """
    url = dataset_info.get('url')
    ds_id = dataset_info.get('id', 'unknown')
    
    if not url:
        logger.warning(f"No URL provided for dataset {ds_id}")
        return False

    logger.info(f"Downloading dataset {ds_id} from {url}...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Determine filename from URL or use ID
        filename = url.split('/')[-1]
        if not filename:
            filename = f"{ds_id}.zip"
        
        local_path = target_dir / filename
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Generate hash and metadata
        file_hash = hash_file(local_path)
        meta = {
            "id": ds_id,
            "source": url,
            "hash": file_hash,
            "type": dataset_info.get('type', 'unknown')
        }
        write_meta(local_path, meta)
        
        logger.info(f"Successfully downloaded and verified {ds_id} ({local_path.name})")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download dataset {ds_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {ds_id}: {e}")
        return False

def verify_data_availability() -> bool:
    """
    Main entry point for data verification.
    
    1. Parses plan.md for verified datasets.
    2. Filters for valid eye-tracking datasets.
    3. If none found, exits with code 1.
    4. If found, downloads them to data/raw/.
    """
    logger.info("Starting data availability verification...")
    
    # Ensure data/raw directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Parse plan.md
    datasets = parse_verified_datasets_block(PLAN_MD_PATH)
    
    if not datasets:
        logger.error("ERROR: No verified datasets found in plan.md. Pipeline cannot proceed.")
        return False

    valid_datasets = [d for d in datasets if is_valid_eye_tracking_dataset(d)]
    
    if not valid_datasets:
        logger.error("ERROR: No verified eye-tracking dataset found. Pipeline cannot proceed.")
        logger.error("All found datasets were either fMRI or lacked eye-tracking indicators.")
        return False

    logger.info(f"Found {len(valid_datasets)} valid eye-tracking dataset(s).")
    
    success_count = 0
    for ds in valid_datasets:
        if download_dataset(ds, DATA_RAW_DIR):
            success_count += 1
    
    if success_count == 0:
        logger.error("ERROR: Failed to download any valid datasets.")
        return False

    logger.info(f"Successfully downloaded {success_count} dataset(s). Verification passed.")
    return True

def main():
    """CLI entry point."""
    success = verify_data_availability()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()