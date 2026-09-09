"""
Download the Moral Machine dataset from the canonical GitHub mirror.

This script fetches the dataset, saves it as a compressed CSV, computes its SHA-256
checksum, and updates the project state file.
"""
import os
import sys
import logging
import hashlib
import yaml
from pathlib import Path
from datetime import datetime, timezone
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/logs/data_validation_log.txt', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
OUTPUT_FILE = DATA_DIR / "moral_machine.csv.gz"
LOG_FILE = PROJECT_ROOT / "results" / "logs" / "data_validation_log.txt"

# URL for the Moral Machine dataset (canonical GitHub mirror)
# Source: https://github.com/soniajoseph/moral-machine-dataset
DATA_URL = "https://raw.githubusercontent.com/soniajoseph/moral-machine-dataset/master/data/moral_machine.csv.gz"

def ensure_directories():
    """Ensure all required directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "results" / "logs").mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_state_file():
    """Ensure the state file exists with basic structure."""
    if not STATE_FILE.exists():
        state_data = {
            "project_id": "PROJ-743-ambient-temperature-influence-on-moral-d",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {},
            "validation_status": {}
        }
        with open(STATE_FILE, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
    return STATE_FILE

def update_state_checksum(checksum: str):
    """Update the state file with the new checksum."""
    state_data = {}
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    state_data["artifact_hashes"]["moral_machine_dataset"] = checksum
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    state_data["validation_status"]["moral_machine_download"] = "success"
    
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def log_success(message: str):
    """Log a success message to the validation log."""
    logger.info(f"[SUCCESS] {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] SUCCESS: {message}\n")

def log_failure(message: str):
    """Log a failure message to the validation log."""
    logger.error(f"[FAILURE] {message}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] FAILURE: {message}\n")

def download_dataset():
    """Download the Moral Machine dataset."""
    logger.info(f"Attempting to download dataset from: {DATA_URL}")
    
    try:
        response = requests.get(DATA_URL, stream=True, timeout=300)
        response.raise_for_status()
        
        logger.info("Download successful. Saving file...")
        with open(OUTPUT_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"File saved to: {OUTPUT_FILE}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download dataset: {e}")
        return False

def main():
    """Main entry point."""
    logger.info("Starting Moral Machine dataset download task (T000)")
    
    # Ensure directories exist
    ensure_directories()
    
    # Ensure state file exists
    ensure_state_file()
    
    # Download dataset
    if not download_dataset():
        log_failure("Failed to download Moral Machine dataset from GitHub mirror.")
        sys.exit(1)
    
    # Verify file exists and is not empty
    if not OUTPUT_FILE.exists() or OUTPUT_FILE.stat().st_size == 0:
        log_failure("Downloaded file is missing or empty.")
        sys.exit(1)
    
    # Compute checksum
    checksum = compute_sha256(OUTPUT_FILE)
    logger.info(f"SHA-256 checksum: {checksum}")
    
    # Update state file
    update_state_checksum(checksum)
    
    # Log success
    log_success(f"Moral Machine dataset downloaded and validated. Checksum: {checksum}")
    logger.info("Task T000 completed successfully.")

if __name__ == "__main__":
    main()
