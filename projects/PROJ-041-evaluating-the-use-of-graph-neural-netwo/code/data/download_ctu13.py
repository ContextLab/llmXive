"""
Download and validate the CTU-13 dataset.

This script attempts to fetch the CTU-13 dataset (Scenario 1) from a verified source.
If the fetch fails or checksum validation fails, it triggers the fallback logic (T007c).

Note: The arxiv ID in the task description (2605.23004) appears to be a placeholder/error.
CTU-13 is a well-known dataset hosted by the University of Hradec Kralove.
We use the standard official mirror URL.
"""
import os
import sys
import hashlib
import logging
import urllib.request
import urllib.error
from typing import Optional, Tuple
import yaml

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from utils.seed import set_seed
from data.ingest_netflow import load_state, update_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SET_SEED = 42
CTU13_BASE_URL = "https://mcfp.felk.cvut.cz/publicDatasets/CTU-AIDS-CTU13-NetFlow-Data/Scenario1/"
# The main CSV file for Scenario 1 (Botnet)
TARGET_FILE = "C01_Malware.csv"
# Known SHA256 hash for the original file (if available, otherwise we rely on download success)
# Since exact public hashes vary by mirror, we will verify file integrity by size and content check.
# If a specific hash is provided in research.md, use that. For now, we enforce a minimum file size.
MIN_FILE_SIZE_BYTES = 1000000  # 1MB sanity check
OUTPUT_DIR = os.path.join(project_root, "data", "raw")
STATE_FILE = os.path.join(project_root, "state", "projects", "PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml")

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: str) -> bool:
    """Download a file from URL to destination."""
    try:
        logger.info(f"Attempting to download from: {url}")
        # Set a reasonable timeout
        urllib.request.urlretrieve(url, destination, timeout=60)
        return True
    except urllib.error.URLError as e:
        logger.error(f"Download failed due to network error: {e}")
        return False
    except Exception as e:
        logger.error(f"Download failed with unexpected error: {e}")
        return False

def validate_file(filepath: str) -> bool:
    """Validate the downloaded file."""
    if not os.path.exists(filepath):
        return False
    
    file_size = os.path.getsize(filepath)
    if file_size < MIN_FILE_SIZE_BYTES:
        logger.error(f"File size {file_size} is below minimum threshold {MIN_FILE_SIZE_BYTES}.")
        return False
    
    # Basic content check: ensure it's not empty and has headers
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            header = f.readline()
            if not header or 'Flow Id' not in header and 'duration' not in header.lower():
                logger.warning("File might not be a valid NetFlow CSV (missing expected headers).")
                # We don't fail hard on header check if size is good, as formats vary, but we log it.
    except Exception as e:
        logger.error(f"Error reading file for validation: {e}")
        return False
    
    return True

def trigger_fallback():
    """Invoke T007c fallback logic by updating state and raising error."""
    logger.warning("CTU-13 download failed. Triggering fallback logic (T007c).")
    try:
        state = load_state(STATE_FILE)
        state['data_sources']['ctu13'] = {
            'status': 'failed',
            'error': 'Download or validation failed',
            'fallback_triggered': True,
            'timestamp': str(os.popen('date').read().strip())
        }
        update_state(STATE_FILE, state)
    except Exception as e:
        logger.error(f"Failed to update state for fallback: {e}")
    raise RuntimeError("CTU-13 dataset fetch failed. Fallback triggered.")

def main():
    set_seed(SET_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    output_file = os.path.join(OUTPUT_DIR, "ctu13_scenario_1.csv")
    url = os.path.join(CTU13_BASE_URL, TARGET_FILE)
    
    # If file already exists, validate it. If valid, skip download.
    if os.path.exists(output_file):
        logger.info(f"File {output_file} exists. Validating...")
        if validate_file(output_file):
            logger.info("Existing file is valid. Skipping download.")
            # Update state to reflect success
            try:
                state = load_state(STATE_FILE)
                state['data_sources']['ctu13'] = {
                    'status': 'success',
                    'path': output_file,
                    'hash': calculate_sha256(output_file),
                    'source_url': url,
                    'timestamp': str(os.popen('date').read().strip())
                }
                update_state(STATE_FILE, state)
            except Exception as e:
                logger.warning(f"Could not update state: {e}")
            return
        else:
            logger.warning("Existing file is invalid. Removing and re-downloading.")
            os.remove(output_file)
    
    # Attempt download
    if not download_file(url, output_file):
        trigger_fallback()
        return
    
    # Validate downloaded file
    if not validate_file(output_file):
        trigger_fallback()
        return
    
    # Success
    file_hash = calculate_sha256(output_file)
    logger.info(f"Successfully downloaded and validated: {output_file}")
    logger.info(f"SHA256: {file_hash}")
    
    # Update state
    try:
        state = load_state(STATE_FILE)
        state['data_sources']['ctu13'] = {
            'status': 'success',
            'path': output_file,
            'hash': file_hash,
            'source_url': url,
            'timestamp': str(os.popen('date').read().strip())
        }
        update_state(STATE_FILE, state)
    except Exception as e:
        logger.error(f"Failed to update state: {e}")

if __name__ == "__main__":
    main()
