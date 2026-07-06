"""
Dataset download and verification module for the cognitive load EEG pipeline.

This module handles the retrieval of the OpenNeuro ds000246 dataset,
verifies the presence of critical files (specifically gaze.tsv),
and manages fallback logic to ds003465 if necessary.
"""
import os
import sys
import hashlib
import json
import subprocess
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import load_config, get_config_value

# Constants
DS000246_ID = "ds000246"
DS003465_ID = "ds003465"
GAZE_FILE = "gaze.tsv"
REQUIRED_FILES = [GAZE_FILE]
STATE_FILE = "state/pipeline_state.yaml"

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Checksum calculation failed: {file_path} not found.")

def download_dataset(dataset_id: str, target_dir: str, config: Dict[str, Any]) -> bool:
    """
    Download a dataset using git-annex or direct download logic.
    For this implementation, we simulate the check for the existence of the directory
    and the critical file, assuming the user has run 'datalad get' or similar externally,
    OR we provide a stub that checks if the data exists locally as per the project's
    data management strategy.

    In a real CI/CD or pipeline run, this would invoke:
    `datalad install -d {target_dir} -s https://github.com/OpenNeuroDatasets/{dataset_id}`
    `datalad get {target_dir}`

    Here we verify the local state.
    """
    dataset_path = Path(target_dir) / dataset_id
    
    if not dataset_path.exists():
        # In a real scenario, we would trigger the download here.
        # For the purpose of this task's verification gate, we check existence.
        print(f"Dataset {dataset_id} not found at {dataset_path}.")
        print("Attempting to trigger download via datalad (if available)...")
        try:
            # Attempt to install and get the dataset
            subprocess.run(
                ["datalad", "install", "-d", str(dataset_path.parent), "-s", f"https://github.com/OpenNeuroDatasets/{dataset_id}"],
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["datalad", "get", str(dataset_path)],
                check=True,
                capture_output=True
            )
            print(f"Successfully downloaded {dataset_id}.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to download {dataset_id} via datalad: {e}")
            return False
        except FileNotFoundError:
            print("Datalad not found. Please install the dataset manually or install datalad.")
            return False

    return True

def verify_dataset_integrity(dataset_path: str, required_files: list) -> bool:
    """
    Verify that all required files exist in the dataset directory.
    Raises FileNotFoundError if critical files are missing.
    """
    missing_files = []
    for file_name in required_files:
        file_path = os.path.join(dataset_path, file_name)
        # Handle nested structures if necessary, but ds000246 typically has gaze.tsv in sub-derivatives or subject folders
        # For ds000246, gaze data is often in sub-*/ses-*/func/ or similar. 
        # We perform a recursive search for the critical file to be robust.
        found = False
        for root, dirs, files in os.walk(dataset_path):
            if file_name in files:
                found = True
                break
        
        if not found:
            missing_files.append(file_name)

    if missing_files:
        raise FileNotFoundError(
            f"Critical files missing in dataset at {dataset_path}: {missing_files}. "
            f"Required: {required_files}. "
            f"Plan: Check spec for fallback to {DS003465_ID}."
        )
    
    return True

def update_state_checksums(dataset_id: str, dataset_path: str, state_path: str):
    """
    Update the pipeline state YAML with checksums and timestamp.
    """
    state_data = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}

    checksums = {}
    for root, dirs, files in os.walk(dataset_path):
        for file in files:
            if file.endswith(('.tsv', '.bdf', '.edf', '.json')):
                full_path = os.path.join(root, file)
                try:
                    checksums[os.path.relpath(full_path, dataset_path)] = calculate_file_checksum(full_path)
                except Exception:
                    pass

    state_data['datasets'] = state_data.get('datasets', {})
    state_data['datasets'][dataset_id] = {
        'path': dataset_path,
        'checksums': checksums,
        'updated_at': __import__('datetime').datetime.now().isoformat()
    }

    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def main():
    """
    Main entry point for the download and verification task (T008).
    Implements the strict verification gate.
    """
    config = load_config()
    data_dir = get_config_value(config, 'data.raw_dir', 'data/raw')
    state_file = get_config_value(config, 'state_file', 'state/pipeline_state.yaml')
    
    print(f"Starting T008: Download and verify {DS000246_ID}...")
    
    # 1. Fetch/Verify ds000246
    target_path = os.path.join(data_dir, DS000246_ID)
    if not download_dataset(DS000246_ID, data_dir, config):
        print(f"Failed to obtain {DS000246_ID}. Checking fallback...")
        # Fallback logic
        print(f"Attempting fallback to {DS003465_ID}...")
        if download_dataset(DS003465_ID, data_dir, config):
            target_path = os.path.join(data_dir, DS003465_ID)
            print(f"Successfully obtained fallback dataset {DS003465_ID}.")
        else:
            raise FileNotFoundError(
                f"CRITICAL: Neither {DS000246_ID} nor fallback {DS003465_ID} could be obtained. "
                "Pipeline cannot proceed."
            )

    # 2. Strict Verification Gate
    try:
        verify_dataset_integrity(target_path, REQUIRED_FILES)
        print(f"Verification PASSED: {GAZE_FILE} found in {target_path}.")
    except FileNotFoundError as e:
        # Re-raise with the specific message required by the task
        raise FileNotFoundError(str(e))

    # 3. Update State
    update_state_checksums(
        DS000246_ID if os.path.exists(os.path.join(data_dir, DS000246_ID)) else DS003465_ID,
        target_path,
        state_file
    )
    print(f"State updated at {state_file}.")
    print("T008 Complete.")

if __name__ == "__main__":
    main()
