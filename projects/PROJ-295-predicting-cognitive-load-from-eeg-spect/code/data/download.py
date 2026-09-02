"""
Download and verify the primary EEG dataset.

This module implements a strict verification gate: it fetches the primary dataset
(OpenNeuro ds000246), checks for the presence of the required 'gaze.tsv' file,
and raises a FileNotFoundError if missing. No automatic fallback is implemented.
"""

import os
import sys
import hashlib
import json
import subprocess
import yaml
import tarfile
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports if running as script
if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
else:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config

# Constants
PRIMARY_DATASET_ID = "ds000246"
FALLBACK_DATASET_ID = "ds003465"
REQUIRED_FILES = ["gaze.tsv"]
DOWNLOAD_TIMEOUT = 300  # 5 minutes for download attempt

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def download_dataset(dataset_id: str, output_dir: str) -> str:
    """
    Download a dataset from OpenNeuro using the datalad command.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000246')
        output_dir: Directory to save the dataset

    Returns:
        Path to the downloaded dataset

    Raises:
        FileNotFoundError: If the dataset cannot be downloaded or is invalid
        RuntimeError: If the download fails
    """
    # Check if datalad is installed
    try:
        subprocess.run(["datalad", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "datalad is not installed. Please install it via: pip install datalad"
        )

    dataset_url = f"https://github.com/OpenNeuroDatasets/{dataset_id}"
    target_path = os.path.join(output_dir, dataset_id)

    print(f"Downloading dataset: {dataset_id} from {dataset_url}")

    # Remove existing directory if it exists
    if os.path.exists(target_path):
        print(f"Removing existing dataset at {target_path}")
        subprocess.run(["rm", "-rf", target_path], check=True)

    # Download using datalad
    try:
        subprocess.run(
            ["datalad", "install", "-d", target_path, dataset_url],
            check=True,
            timeout=DOWNLOAD_TIMEOUT,
            capture_output=True,
            text=True
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Download timed out after {DOWNLOAD_TIMEOUT} seconds")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to download dataset: {e.stderr}")

    return target_path

def verify_dataset_integrity(dataset_path: str, required_files: List[str] = None) -> Dict[str, Any]:
    """
    Verify that the downloaded dataset contains all required files.

    Args:
        dataset_path: Path to the downloaded dataset
        required_files: List of required files (default: REQUIRED_FILES)

    Returns:
        Dictionary with verification results

    Raises:
        FileNotFoundError: If any required file is missing
    """
    if required_files is None:
        required_files = REQUIRED_FILES

    results = {
        "status": "success",
        "message": "All required files found",
        "missing_files": [],
        "found_files": [],
        "checksums": {}
    }

    missing_files = []

    for file_name in required_files:
        file_path = os.path.join(dataset_path, file_name)
        
        # Check if file exists (handle nested structures)
        found = False
        for root, dirs, files in os.walk(dataset_path):
            if file_name in files:
                full_path = os.path.join(root, file_name)
                results["found_files"].append(file_name)
                results["checksums"][file_name] = calculate_file_checksum(full_path)
                found = True
                break

        if not found:
            missing_files.append(file_name)
            results["missing_files"].append(file_name)

    if missing_files:
        error_msg = (
            f"CRITICAL: Required files missing in dataset {dataset_path}: {missing_files}. "
            f"This dataset cannot be used for cognitive load prediction which requires gaze data. "
            f"Please update the spec to use a fallback dataset (e.g., {FALLBACK_DATASET_ID}) "
            f"or manually download the correct dataset."
        )
        raise FileNotFoundError(error_msg)

    return results

def update_state_checksums(output_dir: str, dataset_id: str, results: Dict[str, Any]) -> None:
    """
    Update the project state with dataset checksums.

    Args:
        output_dir: Project output directory
        dataset_id: Dataset ID
        results: Verification results from verify_dataset_integrity
    """
    state_path = os.path.join(output_dir, "state", "dataset_state.yaml")
    
    # Create state directory if it doesn't exist
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    state_data = {
        "dataset_id": dataset_id,
        "checksums": results["checksums"],
        "verification_status": results["status"],
        "verification_message": results["message"],
        "updated_at": "2024-01-01T00:00:00Z"  # Placeholder, would use datetime in real implementation
    }

    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False)

def main():
    """Main entry point for dataset download and verification."""
    # Load configuration
    config = load_config()
    
    # Get paths from config
    data_dir = config.get("paths", {}).get("raw_data", "data/raw")
    output_dir = config.get("paths", {}).get("output", "results")
    
    # Create directories
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Starting dataset download for {PRIMARY_DATASET_ID}")
    print(f"Data directory: {data_dir}")

    try:
        # Download primary dataset
        dataset_path = download_dataset(PRIMARY_DATASET_ID, data_dir)
        
        # Verify integrity
        print(f"Verifying dataset integrity...")
        results = verify_dataset_integrity(dataset_path)
        
        print(f"Verification successful: {results['message']}")
        
        # Update state
        update_state_checksums(output_dir, PRIMARY_DATASET_ID, results)
        
        print(f"Dataset downloaded and verified successfully at: {dataset_path}")
        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"SPEC FLAG: The primary dataset ({PRIMARY_DATASET_ID}) is missing required gaze data.", file=sys.stderr)
        print(f"Please update the specification to use the fallback dataset ({FALLBACK_DATASET_ID}) or manually provide the correct data.", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())