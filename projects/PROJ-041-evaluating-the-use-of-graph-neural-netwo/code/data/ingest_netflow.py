import os
import hashlib
import urllib.request
import urllib.error
import logging
from typing import Optional, Tuple
import shutil

# Configure logging for the ingestion process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join("data", "raw")

# Canonical URLs and Checksums
CTU_URL = "https://zenodo.org/record/4937590/files/CTU-13-dataset.tar.gz"
CTU_CHECKSUM = "e8094024752303026171896721984057"  # Placeholder, replace with actual if known

BOT_IOT_URL = "https://zenodo.org/record/3887642/files/NF-BoT-IoT-v2.zip"
BOT_IOT_CHECKSUM = "a1b2c3d4e5f6789012345678901234567890abcd"  # Placeholder, replace with actual if known

def ensure_data_dirs():
    """Create raw data directories if they do not exist."""
    os.makedirs(DATA_DIR, exist_ok=True)

def _calculate_md5(filepath: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file(url: str, dest_path: str, expected_checksum: Optional[str] = None) -> bool:
    """Download a file from URL and optionally validate checksum."""
    logger.info(f"Downloading {url} to {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Downloaded: {dest_path}")
    except urllib.error.URLError as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

    if expected_checksum:
        actual_checksum = _calculate_md5(dest_path)
        logger.info(f"Checksum verification: Expected={expected_checksum}, Actual={actual_checksum}")
        if actual_checksum.lower() != expected_checksum.lower():
            logger.error(f"Checksum mismatch for {dest_path}!")
            return False
        logger.info("Checksum verified.")
    return True

def download_ctu_dataset() -> Optional[str]:
    """Download CTU dataset if not present."""
    filename = "ctu_dataset.tar.gz"
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        logger.info(f"CTU dataset already exists at {filepath}")
        return filepath
    if download_file(CTU_URL, filepath, CTU_CHECKSUM):
        return filepath
    return None

def download_bot_iot_dataset() -> Optional[str]:
    """Download NF-BoT-IoT dataset if not present."""
    filename = "NF-BoT-IoT-v2.zip"
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        logger.info(f"NF-BoT-IoT dataset already exists at {filepath}")
        return filepath
    if download_file(BOT_IOT_URL, filepath, BOT_IOT_CHECKSUM):
        return filepath
    return None

def main():
    """
    Main entry point implementing T007c fallback logic:
    1. Check CTU availability (download if missing).
    2. If CTU is missing/unavailable, switch to BoT-IoT and log source.
    3. Log the final data source used.
    """
    ensure_data_dirs()
    
    source_used = None
    data_path = None

    # Step 1: Attempt to get CTU dataset
    logger.info("Checking CTU dataset availability...")
    ctu_path = download_ctu_dataset()
    
    if ctu_path:
        source_used = "CTU-13"
        data_path = ctu_path
        logger.info(f"Source selected: {source_used}")
    else:
        logger.warning("CTU dataset unavailable. Initiating fallback to NF-BoT-IoT...")
        # Step 2: Fallback to BoT-IoT
        bot_path = download_bot_iot_dataset()
        if bot_path:
            source_used = "NF-BoT-IoT"
            data_path = bot_path
            logger.info(f"Fallback successful. Source selected: {source_used}")
        else:
            logger.error("Both CTU and NF-BoT-IoT datasets are unavailable. Pipeline cannot proceed.")
            return

    if data_path:
        logger.info(f"Data ingestion complete. Final data path: {data_path}")
        logger.info(f"Final data source: {source_used}")
    else:
        logger.error("Failed to acquire any dataset.")

if __name__ == "__main__":
    main()