"""
Download HCP (ds001734) resting-state fMRI and 2-back behavioral data.

This script fetches rs-fMRI (preprocessed) and task (2-back) data for a
specified number of subjects from OpenNeuro dataset ds001734.
It respects the project's memory constraints and logging infrastructure.
"""
import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests
from tqdm import tqdm

from utils.config import set_all_seeds
from utils.memory_monitor import check_memory_limit, get_memory_usage_report, reset_peak_rss
from utils.logging_config import setup_logging, log_subject_exclusion
from ingestion.validate_source import check_dataset_availability, verify_dataset_structure

# Constants
DATASET_ID = "ds001734"
OPENNEURO_API_URL = "https://api.openneuro.org/datasets"
SUBJECTS_TO_FETCH = 100
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * (1024 ** 3)

# Output directories
RAW_FMRI_DIR = PROJECT_ROOT / "data" / "raw_fmri"
RAW_BEHAV_DIR = PROJECT_ROOT / "data" / "raw_behavior"

# Setup logging
logger = setup_logging()

def get_dataset_files(dataset_id: str) -> Dict[str, List[Dict]]:
    """
    Fetch the file tree for the dataset from OpenNeuro API.
    Returns a dictionary mapping subject IDs to lists of file metadata.
    """
    url = f"{OPENNEURO_API_URL}/{dataset_id}/tree"
    logger.info(f"Fetching file tree from {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch dataset tree: {e}")
        raise

    # Parse the tree structure
    # OpenNeuro API returns a nested structure or a flat list depending on version.
    # We expect a list of files with 'path' and 'id'.
    files = data.get("files", [])
    
    # Organize by subject
    subjects_files = {}
    
    for f in files:
        path = f.get("path", "")
        # HCP data structure: sub-XXXXXX/...
        if "sub-" in path:
            parts = path.split("/")
            subject_id = parts[0] # e.g., "sub-100004"
            
            if subject_id not in subjects_files:
                subjects_files[subject_id] = []
            
            subjects_files[subject_id].append(f)
    
    return subjects_files

def filter_subject_files(
    subject_files: List[Dict], 
    task_type: str = "rest"
) -> List[Dict]:
    """
    Filter files for a specific subject based on task type.
    task_type: 'rest' for resting-state, 'nback' for 2-back task.
    """
    filtered = []
    for f in subject_files:
        path = f.get("path", "")
        if task_type == "rest":
            if "rfMRI" in path and "Preprocessed" in path:
                filtered.append(f)
        elif task_type == "nback":
            if "tfMRI" in path and "nback" in path:
                filtered.append(f)
    return filtered

def download_file(
    file_metadata: Dict, 
    dest_dir: Path, 
    base_url: str = "https://openneuro.org/datasets"
) -> bool:
    """
    Download a single file from OpenNeuro.
    Returns True if successful, False otherwise.
    """
    # OpenNeuro download URLs are typically constructed or retrieved via a specific endpoint.
    # For ds001734, we often need the direct s3 link or the openneuro download link.
    # The API usually provides a 'url' or we construct it.
    # However, the /tree endpoint doesn't give direct download URLs.
    # We use the standard OpenNeuro download pattern: 
    # https://openneuro.org/datasets/{dataset_id}/versions/{version}/download?file={file_id}
    # OR we rely on the fact that the 'id' in the tree is the file ID.
    
    # A more robust way for OpenNeuro API v3 is to use the download endpoint.
    # But often, for large datasets, we use the s3 bucket directly if public.
    # ds001734 is public.
    
    # Let's try to construct the download URL based on the file ID.
    # The 'id' in the tree response is the file ID.
    file_id = file_metadata.get("id")
    filename = file_metadata.get("path", "").split("/")[-1]
    
    # OpenNeuro download API endpoint for a specific file
    # Note: This might require a different approach if the API doesn't expose direct links easily.
    # Alternative: Use the openneuro-py library if available, but we are using requests.
    # We will try to fetch the download link from the file endpoint if possible, 
    # or construct it.
    
    # Since direct file download links aren't always in the tree, 
    # we will use the generic download endpoint pattern if we can't get a direct link.
    # However, for simplicity in this script without the full openneuro-py client logic,
    # we will assume we can construct the URL or the API provides it.
    # Let's assume the 'id' is sufficient to construct a download URL for the public bucket.
    # ds001734 is on S3: s3://openneuro-datasets/ds001734/...
    # We can try the public S3 URL construction.
    
    # Base S3 URL for ds001734
    # Path in tree: sub-XXXXXX/...
    # S3 path: ds001734/sub-XXXXXX/...
    s3_path = f"https://openneuro-datasets.s3.amazonaws.com/ds001734/{file_metadata['path']}"
    
    dest_path = dest_dir / filename
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Downloading {filename} from {s3_path}")

    try:
        # Stream download to handle large files
        response = requests.get(s3_path, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024 # 1MB
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=filename,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
                    # Check memory periodically
                    if pbar.n % (block_size * 10) == 0:
                        check_memory_limit(MEMORY_LIMIT_BYTES)
        
        logger.info(f"Successfully downloaded {filename}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download {filename}: {e}")
        return False

def download_subject_data(
    subject_id: str, 
    subject_files: List[Dict], 
    force_download: bool = False
) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Download rs-fMRI and 2-back data for a single subject.
    Returns paths to downloaded directories (or None if failed).
    """
    # Filter files
    rest_files = filter_subject_files(subject_files, "rest")
    nback_files = filter_subject_files(subject_files, "nback")

    if not rest_files:
        logger.warning(f"No resting-state files found for {subject_id}")
        return None, None
    
    if not nback_files:
        logger.warning(f"No 2-back files found for {subject_id}")
        return None, None

    # Create subject directories
    subj_fmri_dir = RAW_FMRI_DIR / subject_id
    subj_behav_dir = RAW_BEHAV_DIR / subject_id
    subj_fmri_dir.mkdir(parents=True, exist_ok=True)
    subj_behav_dir.mkdir(parents=True, exist_ok=True)

    all_success = True

    # Download fMRI
    for f in rest_files:
        if not download_file(f, subj_fmri_dir):
            all_success = False
    
    # Download behavior (nback)
    for f in nback_files:
        if not download_file(f, subj_behav_dir):
            all_success = False

    if all_success:
        return subj_fmri_dir, subj_behav_dir
    else:
        return None, None

def main():
    """
    Main entry point for downloading HCP data.
    """
    logger.info(f"Starting download for {DATASET_ID}")
    logger.info(f"Target subjects: {SUBJECTS_TO_FETCH}")
    logger.info(f"Memory limit: {MEMORY_LIMIT_GB} GB")

    # Initialize directories
    RAW_FMRI_DIR.mkdir(parents=True, exist_ok=True)
    RAW_BEHAV_DIR.mkdir(parents=True, exist_ok=True)

    # Validate source availability
    if not check_dataset_availability(DATASET_ID):
        logger.error(f"Dataset {DATASET_ID} is not available.")
        sys.exit(1)

    # Fetch file tree
    try:
        all_subjects_files = get_dataset_files(DATASET_ID)
    except Exception as e:
        logger.error(f"Failed to retrieve file tree: {e}")
        sys.exit(1)

    # Sort subjects and select first N
    sorted_subjects = sorted(all_subjects_files.keys())
    selected_subjects = sorted_subjects[:SUBJECTS_TO_FETCH]
    
    logger.info(f"Selected {len(selected_subjects)} subjects for download.")

    downloaded_count = 0
    failed_count = 0

    reset_peak_rss()

    for i, subj_id in enumerate(selected_subjects):
        logger.info(f"[{i+1}/{len(selected_subjects)}] Processing {subj_id}")
        
        # Check memory before each subject
        if not check_memory_limit(MEMORY_LIMIT_BYTES):
            logger.error("Memory limit exceeded. Aborting.")
            break

        fmri_path, behav_path = download_subject_data(subj_id, all_subjects_files[subj_id])
        
        if fmri_path and behav_path:
            downloaded_count += 1
        else:
            failed_count += 1
            log_subject_exclusion(subj_id, reason="Download failure")

        # Small delay to be polite to the server
        time.sleep(0.5)

    logger.info(f"Download complete. Success: {downloaded_count}, Failed: {failed_count}")
    logger.info(f"Peak memory usage: {get_memory_usage_report()}")

    if failed_count > 0:
        logger.warning(f"Some subjects failed to download. Check logs.")
        # Do not exit with error if at least some were downloaded, 
        # but this might be configurable. For now, we log warning.

if __name__ == "__main__":
    main()