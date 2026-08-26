"""
Data Ingestion Module for Network Traffic Anomaly Detection.

Handles downloading of CTU and NF-BoT-IoT datasets, validates checksums,
and manages fallback logic between datasets.
"""
import os
import hashlib
import urllib.request
import urllib.error
import logging
import yaml
from typing import Optional, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(PROJECT_ROOT, "state", "projects")
STATE_FILE = os.path.join(
    STATE_DIR,
    "PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml"
)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

# Dataset configurations
CTU_CONFIG = {
    "name": "CTU-13",
    "url": "https://stratosphereips.org/datasets/ctu13-dataset-2.1.zip",
    "checksum": "d41d8cd98f00b204e9800998ecf8427e",  # Placeholder, updated by T007a
    "description": "CTU-13 Botnet Traffic Dataset"
}

BOT_IOT_CONFIG = {
    "name": "NF-BoT-IoT",
    "url": "https://nd.edu.pl/~jblazek/NF-BoT-IoT.zip",
    "checksum": "e4d909c290d0fb1ca068ffaddf22cbd0",  # Placeholder, updated by T007b
    "description": "NF-BoT-IoT Dataset"
}

def ensure_data_dirs():
    """Ensure required directories exist."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)
    logger.info(f"Ensured data directories: {RAW_DATA_DIR}, {STATE_DIR}")

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file(url: str, dest_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Download a file from a URL and optionally validate checksum.

    Args:
        url: The URL to download from.
        dest_path: Local path to save the file.
        expected_checksum: Optional MD5 checksum to validate against.

    Returns:
        True if download and validation successful, False otherwise.
    """
    try:
        logger.info(f"Downloading {url} to {dest_path}")
        urllib.request.urlretrieve(url, dest_path)

        if expected_checksum:
            actual_checksum = calculate_md5(dest_path)
            if actual_checksum != expected_checksum:
                logger.error(
                    f"Checksum mismatch for {dest_path}. "
                    f"Expected: {expected_checksum}, Got: {actual_checksum}"
                )
                os.remove(dest_path)
                return False
            logger.info(f"Checksum validated: {actual_checksum}")

        return True
    except urllib.error.URLError as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return False

def download_ctu_dataset() -> Tuple[bool, str]:
    """
    Attempt to download the CTU dataset.

    Returns:
        Tuple of (success: bool, message: str)
    """
    filename = os.path.basename(CTU_CONFIG["url"])
    dest_path = os.path.join(RAW_DATA_DIR, filename)

    if os.path.exists(dest_path):
        logger.info(f"CTU dataset already exists at {dest_path}")
        return True, "CTU dataset already exists."

    success = download_file(CTU_CONFIG["url"], dest_path, CTU_CONFIG["checksum"])
    if success:
        return True, f"Successfully downloaded CTU dataset to {dest_path}"
    else:
        return False, "Failed to download CTU dataset."

def download_bot_iot_dataset() -> Tuple[bool, str]:
    """
    Attempt to download the NF-BoT-IoT dataset.

    Returns:
        Tuple of (success: bool, message: str)
    """
    filename = os.path.basename(BOT_IOT_CONFIG["url"])
    dest_path = os.path.join(RAW_DATA_DIR, filename)

    if os.path.exists(dest_path):
        logger.info(f"NF-BoT-IoT dataset already exists at {dest_path}")
        return True, "NF-BoT-IoT dataset already exists."

    success = download_file(BOT_IOT_CONFIG["url"], dest_path, BOT_IOT_CONFIG["checksum"])
    if success:
        return True, f"Successfully downloaded NF-BoT-IoT dataset to {dest_path}"
    else:
        return False, "Failed to download NF-BoT-IoT dataset."

def load_state() -> Dict[str, Any]:
    """Load the project state YAML file."""
    if not os.path.exists(STATE_FILE):
        return {
            "project_id": "PROJ-041-evaluating-the-use-of-graph-neural-netwo",
            "artifact_hashes": {},
            "dataset_info": {},
            "updated_at": None
        }
    try:
        with open(STATE_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Could not load state file {STATE_FILE}: {e}")
        return {
            "project_id": "PROJ-041-evaluating-the-use-of-graph-neural-netwo",
            "artifact_hashes": {},
            "dataset_info": {},
            "updated_at": None
        }

def update_state(dataset_name: str, url: str, version: str, checksum: str):
    """
    Update the project state file with dataset information.

    This is the Single Source of Truth for the active dataset.

    Args:
        dataset_name: Name of the dataset (e.g., 'CTU-13', 'NF-BoT-IoT')
        url: The URL used to download the dataset
        version: Version string of the dataset
        checksum: The validated checksum of the downloaded file
    """
    state = load_state()
    state["dataset_info"] = {
        "active_dataset": dataset_name,
        "url": url,
        "version": version,
        "checksum": checksum
    }
    # Update timestamp
    import datetime
    state["updated_at"] = datetime.datetime.now().isoformat()

    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Updated state file {STATE_FILE} with dataset info: {dataset_name}")

def main():
    """
    Main entry point for data ingestion with fallback logic.

    1. Try to download CTU dataset.
    2. If CTU fails or missing, fallback to NF-BoT-IoT.
    3. Upon successful download, update state.yaml with the active dataset info.
    """
    ensure_data_dirs()

    # Attempt CTU
    ctu_success, ctu_msg = download_ctu_dataset()
    if ctu_success:
        logger.info(f"CTU Success: {ctu_msg}")
        # Update state with CTU info
        # Note: In a real scenario, version and checksum would be dynamic or retrieved from a manifest
        update_state(
            dataset_name=CTU_CONFIG["name"],
            url=CTU_CONFIG["url"],
            version="2.1",
            checksum=calculate_md5(os.path.join(RAW_DATA_DIR, os.path.basename(CTU_CONFIG["url"])))
        )
        return 0

    logger.warning(f"CTU Failed: {ctu_msg}")
    logger.info("Attempting fallback to NF-BoT-IoT dataset...")

    # Fallback to BoT-IoT
    bot_success, bot_msg = download_bot_iot_dataset()
    if bot_success:
        logger.info(f"BoT-IoT Success: {bot_msg}")
        # Update state with BoT-IoT info
        update_state(
            dataset_name=BOT_IOT_CONFIG["name"],
            url=BOT_IOT_CONFIG["url"],
            version="1.0",
            checksum=calculate_md5(os.path.join(RAW_DATA_DIR, os.path.basename(BOT_IOT_CONFIG["url"])))
        )
        return 0

    logger.error("Both CTU and NF-BoT-IoT downloads failed. Aborting.")
    return 1

if __name__ == "__main__":
    exit(main())