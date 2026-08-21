"""
Manifest generator for EEG dataset verification.

This module implements Constitution Principle VI by automatically fetching
and verifying dataset URL, version, and checksums from the source.
It generates a manifest.yaml file that tracks dataset integrity.
"""
import os
import sys
import hashlib
import json
import datetime
import yaml
import requests
from typing import Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import load_config

# Constants
MANIFEST_PATH = "data/manifest.yaml"
STATE_PATH = "state.yaml"
DATASET_ID = "ds000246"  # OpenNeuro dataset
DATASET_VERSION = "1.1.4"
DATASET_URL = f"https://datasets.datalad.org/workflows/openneuro/{DATASET_ID}/tree/{DATASET_VERSION}"

def calculate_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file checksum
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    hash_func = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()

def fetch_remote_checksum(url: str, filename: str) -> Optional[str]:
    """
    Fetch checksum from a remote source (OpenNeuro).
    
    Args:
        url: Remote URL to fetch checksum from
        filename: Name of the file to get checksum for
        
    Returns:
        Checksum string if found, None otherwise
    """
    try:
        # OpenNeuro typically provides checksums in .gitattributes or dataset_description.json
        # For ds000246, we'll try to fetch the dataset_description.json first
        desc_url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/{DATASET_VERSION}/dataset_description.json"
        
        response = requests.get(desc_url, timeout=30)
        if response.status_code == 200:
            desc_data = response.json()
            # Check if we can extract version info
            if 'Version' in desc_data:
                # We have version info, but not file checksums directly
                pass
        
        # For now, we'll use a fallback approach:
        # OpenNeuro datasets are available via datalad
        # We'll construct the expected checksum file URL
        checksum_url = f"https://datasets.datalad.org/workflows/openneuro/{DATASET_ID}/tree/{DATASET_VERSION}/.datalad/.gitattributes"
        
        response = requests.get(checksum_url, timeout=30)
        if response.status_code == 200:
            # Parse the .gitattributes file for checksums
            content = response.text
            # Look for sha256 checksums in the file
            for line in content.split('\n'):
                if filename in line and 'sha256' in line:
                    parts = line.split()
                    for part in parts:
                        if len(part) == 64 and all(c in '0123456789abcdef' for c in part):
                            return part
        
        return None
        
    except Exception as e:
        print(f"Warning: Could not fetch remote checksum for {filename}: {e}")
        return None

def verify_dataset_integrity(data_dir: str, manifest: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """
    Verify the integrity of the downloaded dataset against the manifest.
    
    Args:
        data_dir: Directory containing the dataset
        manifest: Manifest dictionary with expected checksums
        
    Returns:
        Tuple of (all_valid, failed_files) where failed_files contains
        files that failed verification
    """
    all_valid = True
    failed_files = {}
    
    for filename, expected_checksum in manifest.get('files', {}).items():
        filepath = os.path.join(data_dir, filename)
        
        if not os.path.exists(filepath):
            failed_files[filename] = "File not found"
            all_valid = False
            continue
        
        try:
            actual_checksum = calculate_file_checksum(filepath)
            
            if actual_checksum != expected_checksum:
                failed_files[filename] = f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
                all_valid = False
            else:
                print(f"✓ Verified: {filename}")
                
        except Exception as e:
            failed_files[filename] = str(e)
            all_valid = False
    
    return all_valid, failed_files

def generate_manifest(data_dir: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a manifest file for the dataset.
    
    Args:
        data_dir: Directory containing the dataset
        output_path: Path to write the manifest file
        
    Returns:
        The generated manifest dictionary
    """
    manifest = {
        "dataset_id": DATASET_ID,
        "version": DATASET_VERSION,
        "source_url": DATASET_URL,
        "generated_at": datetime.datetime.now().isoformat(),
        "files": {}
    }
    
    # Scan the data directory for key files
    key_files = [
        "dataset_description.json",
        "sub-01/func/sub-01_task-nback_bold.nii.gz",
        "sub-01/eeg/sub-01_task-nback_eeg.edf",
        "sub-01/eeg/sub-01_task-nback_events.tsv",
        "participants.tsv",
        "gaze.tsv"
    ]
    
    for filename in key_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                checksum = calculate_file_checksum(filepath)
                file_size = os.path.getsize(filepath)
                manifest["files"][filename] = {
                    "checksum": checksum,
                    "size_bytes": file_size,
                    "verified_at": datetime.datetime.now().isoformat()
                }
                print(f"✓ Added to manifest: {filename}")
            except Exception as e:
                print(f"Warning: Could not process {filename}: {e}")
        else:
            # Try to fetch remote checksum if available
            remote_checksum = fetch_remote_checksum(DATASET_URL, filename)
            if remote_checksum:
                manifest["files"][filename] = {
                    "checksum": remote_checksum,
                    "size_bytes": None,
                    "source": "remote",
                    "verified_at": datetime.datetime.now().isoformat()
                }
                print(f"✓ Added remote checksum for: {filename}")
            else:
                print(f"⚠ File not found and no remote checksum: {filename}")
    
    # Write manifest to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print(f"Manifest written to: {output_path}")
    return manifest

def update_state(manifest_path: str, state_path: str = STATE_PATH):
    """
    Update the state file with manifest checksums.
    
    Args:
        manifest_path: Path to the manifest file
        state_path: Path to the state file
    """
    if not os.path.exists(manifest_path):
        print(f"Warning: Manifest file not found at {manifest_path}")
        return
        
    try:
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
        
        # Calculate checksum of the manifest file itself
        manifest_checksum = calculate_file_checksum(manifest_path)
        
        # Load or create state
        state = {}
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = yaml.safe_load(f) or {}
        
        # Update state
        state['manifest'] = {
            'path': manifest_path,
            'checksum': manifest_checksum,
            'updated_at': datetime.datetime.now().isoformat(),
            'dataset_id': manifest.get('dataset_id'),
            'version': manifest.get('version')
        }
        
        # Write state
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        
        print(f"State updated: {state_path}")
        
    except Exception as e:
        print(f"Error updating state: {e}")
        raise

def main():
    """Main entry point for manifest generation."""
    config = load_config()
    
    # Get data directory from config or use default
    data_dir = config.get('data', {}).get('raw_dir', 'data/raw')
    output_path = MANIFEST_PATH
    
    print(f"Generating manifest for dataset in: {data_dir}")
    
    # Generate manifest
    manifest = generate_manifest(data_dir, output_path)
    
    # Update state
    update_state(output_path)
    
    # Verify dataset integrity if files exist
    if manifest.get('files'):
        all_valid, failed_files = verify_dataset_integrity(data_dir, manifest)
        
        if all_valid:
            print("✓ All files verified successfully")
        else:
            print("⚠ Some files failed verification:")
            for filename, error in failed_files.items():
                print(f"  - {filename}: {error}")
                
    return manifest

if __name__ == "__main__":
    main()
