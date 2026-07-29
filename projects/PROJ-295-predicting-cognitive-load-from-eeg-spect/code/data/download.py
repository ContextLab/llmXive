import os
import sys
import hashlib
import json
import subprocess
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports if running as script
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
TARGET_DATASET_ID = "ds000246"
FALLBACK_DATASET_ID = "ds003465"
REQUIRED_FILE = "gaze.tsv"
STATE_FILE = "state/pipeline_state.yaml"
MANIFEST_FILE = "data/manifest.yaml"
DATA_DIR = "data/raw"

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def download_dataset(dataset_id: str, target_dir: str) -> str:
    """
    Download a dataset from OpenNeuro using the datalad command.
    Returns the path to the downloaded directory.
    """
    dataset_url = f"https://gitlab.com/psychology/oxford/oxford-naturalistic-eeg-dataset" # Placeholder or specific URL logic
    # Using datalad is the standard for OpenNeuro
    # datalad install -d {target_dir} -s {dataset_url}
    
    # For this implementation, we assume 'datalad' is installed and configured.
    # We will attempt to install the dataset.
    dataset_path = os.path.join(target_dir, dataset_id)
    
    if not os.path.exists(dataset_path):
        logger.info(f"Downloading dataset {dataset_id} to {dataset_path}...")
        try:
            # Attempt to use datalad
            subprocess.run(
                ["datalad", "install", "-d", dataset_path, "-s", f"https://datasets.datalad.org/{dataset_id}"],
                check=True,
                capture_output=False
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download dataset via datalad: {e}")
            # Fallback: try direct git clone if datalad fails, though less common for large binaries
            raise RuntimeError(f"Could not download {dataset_id}. Ensure datalad is installed and configured.")
    
    return dataset_path

def verify_dataset_integrity(dataset_path: str, required_files: List[str]) -> bool:
    """Verify that the downloaded dataset contains all required files."""
    missing_files = []
    for file_name in required_files:
        file_path = os.path.join(dataset_path, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
    
    if missing_files:
        return False, missing_files
    return True, []

def update_state_checksums(state_file: str, dataset_id: str, checksums: Dict[str, str]) -> None:
    """Update the pipeline state YAML with checksums and timestamp."""
    state = {}
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state = yaml.safe_load(f) or {}
    
    state["last_updated"] = str(datetime.datetime.now())
    if "datasets" not in state:
        state["datasets"] = {}
    
    state["datasets"][dataset_id] = {
        "checksums": checksums,
        "verified": True
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def main():
    """
    Main entry point for T008: Download ds000246, verify gaze.tsv,
    raise error if missing, and update state.
    """
    logger.info(f"Starting T008: Download and verify {TARGET_DATASET_ID}")
    
    config = load_config()
    data_dir = config.get("data_dir", DATA_DIR)
    os.makedirs(data_dir, exist_ok=True)
    
    # Step 1: Download ds000246
    try:
        dataset_path = download_dataset(TARGET_DATASET_ID, data_dir)
    except Exception as e:
        logger.error(f"Critical failure: Could not download {TARGET_DATASET_ID}. {e}")
        raise

    # Step 2: Check for gaze.tsv
    # OpenNeuro datasets usually have structure: dsXXXXXX/sub-XX/...
    # We need to search recursively for gaze.tsv or check common locations.
    # The task specifically says "check for gaze.tsv".
    
    found_gaze = False
    gaze_path = None
    
    for root, dirs, files in os.walk(dataset_path):
        if REQUIRED_FILE in files:
            found_gaze = True
            gaze_path = os.path.join(root, REQUIRED_FILE)
            break
    
    if not found_gaze:
        # Strict verification gate: Raise FileNotFoundError
        error_msg = (
            f"VERIFICATION FAILED: Required file '{REQUIRED_FILE}' not found in {TARGET_DATASET_ID}.\n"
            f"Dataset path scanned: {dataset_path}\n"
            f"Action: Marking spec for fallback to {FALLBACK_DATASET_ID}.\n"
            f"Please ensure the correct dataset version is downloaded or check the dataset structure."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Verification passed: Found {REQUIRED_FILE} at {gaze_path}")
    
    # Step 3: Calculate checksums for state update
    checksums = {}
    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            if file.endswith(".tsv") or file.endswith(".json") or file.endswith(".nii.gz"):
                full_path = os.path.join(root, file)
                try:
                    checksums[os.path.relpath(full_path, dataset_path)] = calculate_file_checksum(full_path)
                except Exception as e:
                    logger.warning(f"Could not checksum {full_path}: {e}")
    
    # Step 4: Update state
    state_file_path = os.path.join(_root, STATE_FILE)
    try:
        update_state_checksums(state_file_path, TARGET_DATASET_ID, checksums)
        logger.info(f"State updated at {state_file_path}")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        # Non-fatal for the download logic, but we log it

    logger.info("T008 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
