"""
Download script for ds000228.

Fetches NIfTI files for subjects listed in data/raw/valid_subjects.json.
Uses OpenNeuro CLI (via pynv) or direct requests if CLI is unavailable.
This implementation uses the OpenNeuro API to fetch file URLs and downloads them.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import urljoin
import hashlib
import shutil
import tarfile
import gzip
from io import BytesIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceededError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "ds000228"
OPENNEURO_API_BASE = "https://api.openneuro.org"
OUTPUT_DIR = Path("data/raw")
VALID_SUBJECTS_FILE = Path("data/raw/valid_subjects.json")
MEMORY_LIMIT_GB = 7

def get_dataset_metadata() -> Dict[str, Any]:
    """Fetch dataset metadata from OpenNeuro API."""
    url = f"{OPENNEURO_API_BASE}/datasets/{DATASET_ID}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch dataset metadata: {e}")
        raise

def get_subject_files(subject_id: str) -> List[Dict[str, Any]]:
    """
    Get list of NIfTI files for a specific subject from OpenNeuro.
    
    Returns a list of dicts with 'filename', 'url', 'size' keys.
    """
    # OpenNeuro API endpoint for files
    url = f"{OPENNEURO_API_BASE}/datasets/{DATASET_ID}/files"
    params = {
        'prefix': f"sub-{subject_id}",
        'suffix': 'nii.gz',
        'type': 'raw'
    }
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        files = response.json()
        
        nifti_files = []
        for f in files:
            if f.get('filename', '').endswith('.nii.gz'):
                nifti_files.append({
                    'filename': f['filename'],
                    'url': f.get('url', ''),
                    'size': f.get('size', 0)
                })
        
        return nifti_files
    except requests.RequestException as e:
        logger.error(f"Failed to fetch files for subject {subject_id}: {e}")
        return []

def download_file(url: str, dest_path: Path, memory_monitor: MemoryMonitor) -> bool:
    """
    Download a file from URL to dest_path with memory monitoring.
    
    Returns True if successful, False otherwise.
    """
    try:
        # Stream the download to avoid loading entire file into memory
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(dest_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Check memory periodically
                        if downloaded % (10 * 1024 * 1024) == 0:  # Every 10MB
                            memory_monitor.check()
                            
            logger.info(f"Downloaded {dest_path.name} ({downloaded / 1024 / 1024:.1f} MB)")
            return True
            
    except MemoryLimitExceededError:
        logger.error(f"Memory limit exceeded while downloading {url}")
        raise
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

def load_valid_subjects() -> List[str]:
    """Load the list of valid subject IDs from the filtered subjects file."""
    if not VALID_SUBJECTS_FILE.exists():
        raise FileNotFoundError(
            f"Valid subjects file not found: {VALID_SUBJECTS_FILE}. "
            "Run filter_subjects.py first."
        )
    
    with open(VALID_SUBJECTS_FILE, 'r') as f:
        data = json.load(f)
    
    if 'subjects' not in data:
        raise ValueError("Invalid format in valid_subjects.json: missing 'subjects' key")
    
    return data['subjects']

def ensure_output_dir():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Create subdirectory for this dataset
    (OUTPUT_DIR / DATASET_ID).mkdir(exist_ok=True)

def main():
    """Main download routine."""
    logger.info(f"Starting download for dataset {DATASET_ID}")
    
    # Initialize memory monitor
    memory_monitor = MemoryMonitor(limit_gb=MEMORY_LIMIT_GB)
    memory_monitor.start()
    
    try:
        # Load valid subjects
        subject_ids = load_valid_subjects()
        logger.info(f"Found {len(subject_ids)} valid subjects to download")
        
        if not subject_ids:
            logger.warning("No subjects to download. Exiting.")
            return
        
        # Ensure output directory exists
        ensure_output_dir()
        
        # Download files for each subject
        total_downloaded = 0
        failed_downloads = []
        
        for i, subject_id in enumerate(subject_ids):
            logger.info(f"Processing subject {i+1}/{len(subject_ids)}: {subject_id}")
            
            try:
                memory_monitor.check()
                
                # Get file list for this subject
                files = get_subject_files(subject_id)
                
                if not files:
                    logger.warning(f"No NIfTI files found for subject {subject_id}")
                    continue
                
                subject_dir = OUTPUT_DIR / DATASET_ID / f"sub-{subject_id}"
                subject_dir.mkdir(parents=True, exist_ok=True)
                
                subject_success = 0
                for file_info in files:
                    filename = file_info['filename']
                    url = file_info['url']
                    dest_path = subject_dir / filename
                    
                    if dest_path.exists():
                        logger.info(f"Skipping existing file: {filename}")
                        subject_success += 1
                        continue
                    
                    if download_file(url, dest_path, memory_monitor):
                        subject_success += 1
                        total_downloaded += 1
                    else:
                        failed_downloads.append(f"{subject_id}/{filename}")
                
                logger.info(f"Subject {subject_id}: {subject_success}/{len(files)} files downloaded")
                
            except MemoryLimitExceededError:
                logger.error(f"Memory limit exceeded during subject {subject_id} download. Aborting.")
                break
            except Exception as e:
                logger.error(f"Error processing subject {subject_id}: {e}")
                failed_downloads.append(f"{subject_id}/general_error")
        
        # Summary
        logger.info(f"Download complete. Total files downloaded: {total_downloaded}")
        if failed_downloads:
            logger.warning(f"Failed downloads: {len(failed_downloads)}")
            for item in failed_downloads[:10]:  # Log first 10 failures
                logger.warning(f"  - {item}")
            if len(failed_downloads) > 10:
                logger.warning(f"  ... and {len(failed_downloads) - 10} more")
        
    finally:
        memory_monitor.stop()
        logger.info("Download process finished")

if __name__ == "__main__":
    main()
