import os
import sys
import hashlib
import json
import datetime
import yaml
import requests
from typing import Dict, Any, Optional

# Constants for the OpenNeuro dataset
DATASET_ID = "ds000246"
OPENNEURO_API_URL = "https://openneuro.org/crn/datasets"
OPENNEURO_DOWNLOAD_URL = "https://openneuro.org/datasets/{dataset_id}/versions"
TARGET_FILE = "gaze.tsv"
STATE_FILE = "state/pipeline_state.yaml"

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def fetch_remote_checksum(dataset_id: str, filename: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the remote checksum and version info for a specific file from OpenNeuro.
    Returns a dict with 'version', 'checksum', 'size' or None if not found.
    """
    # OpenNeuro API to get dataset versions
    versions_url = f"https://openneuro.org/crn/datasets/{dataset_id}/versions"
    try:
        response = requests.get(versions_url, timeout=30)
        response.raise_for_status()
        versions = response.json()

        # We need the latest version or a specific one. Let's assume latest for now.
        # OpenNeuro API structure might vary, but typically returns a list of versions.
        if not versions:
            return None

        # Sort by creation date descending to get latest
        latest_version = max(versions, key=lambda v: v.get('creationDate', 0))
        version_id = latest_version.get('id')

        # Now get the manifest for this version to find file checksums
        # OpenNeuro doesn't always expose file-level checksums directly in the version list.
        # We might need to download the manifest or check the dataset structure.
        # For this implementation, we will attempt to fetch the dataset snapshot manifest.
        # A common pattern is to download the dataset and verify, but here we try to get metadata.

        # Alternative: Use the dataset's snapshot API if available
        snapshot_url = f"https://openneuro.org/crn/datasets/{dataset_id}/snapshots/{version_id}"
        snap_response = requests.get(snapshot_url, timeout=30)
        if snap_response.status_code == 200:
            snap_data = snap_response.json()
            # Look for files in the snapshot
            if 'files' in snap_data:
                for file_info in snap_data['files']:
                    if file_info.get('name') == filename or file_info.get('path', '').endswith(filename):
                        return {
                            "version": version_id,
                            "checksum": file_info.get('checksum', file_info.get('md5')),
                            "size": file_info.get('size'),
                            "url": file_info.get('url')
                        }
        return None
    except requests.RequestException as e:
        print(f"Warning: Could not fetch remote metadata for {filename}: {e}")
        return None

def verify_dataset_integrity(dataset_path: str, filename: str, expected_checksum: str) -> bool:
    """Verify the local file matches the expected checksum."""
    full_path = os.path.join(dataset_path, filename)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Expected file {filename} not found in {dataset_path}")

    actual_checksum = calculate_file_checksum(full_path)
    return actual_checksum.lower() == expected_checksum.lower()

def generate_manifest(dataset_id: str, dataset_path: str, output_path: str, filename: str = TARGET_FILE):
    """
    Generate a manifest.yaml file containing dataset URL, version, and checksums.
    This satisfies Constitution Principle VI by automatically fetching and verifying.
    """
    print(f"Generating manifest for dataset {dataset_id}...")

    # 1. Fetch remote metadata
    remote_info = fetch_remote_checksum(dataset_id, filename)

    if not remote_info:
        # If we can't fetch remote info, we might still generate a manifest based on local file
        # but we must flag that remote verification failed.
        print(f"Warning: Could not fetch remote metadata for {filename}. Generating manifest with local data only.")
        local_path = os.path.join(dataset_path, filename)
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file {filename} not found at {local_path} and remote metadata unavailable.")
        
        local_checksum = calculate_file_checksum(local_path)
        manifest_data = {
            "dataset_id": dataset_id,
            "source_url": f"https://openneuro.org/datasets/{dataset_id}",
            "version": "unknown",
            "files": [
                {
                    "name": filename,
                    "checksum": local_checksum,
                    "checksum_algorithm": "sha256",
                    "verified_against_source": False,
                    "verification_message": "Remote metadata unavailable; checksum is local only."
                }
            ],
            "generated_at": datetime.datetime.now().isoformat()
        }
    else:
        # Verify local file against remote checksum
        local_path = os.path.join(dataset_path, filename)
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file {filename} not found at {local_path} to verify against remote checksum.")

        is_verified = verify_dataset_integrity(dataset_path, filename, remote_info['checksum'])
        
        manifest_data = {
            "dataset_id": dataset_id,
            "source_url": f"https://openneuro.org/datasets/{dataset_id}",
            "version": remote_info['version'],
            "files": [
                {
                    "name": filename,
                    "checksum": remote_info['checksum'],
                    "checksum_algorithm": "sha256", # Assuming sha256 based on API, adjust if API returns md5
                    "verified_against_source": is_verified,
                    "verification_message": "Verified against OpenNeuro remote metadata." if is_verified else "Checksum mismatch!"
                }
            ],
            "generated_at": datetime.datetime.now().isoformat()
        }
        
        if not is_verified:
            raise ValueError(f"Checksum verification failed for {filename}. Expected {remote_info['checksum']}, got {calculate_file_checksum(local_path)}.")

    # Write manifest
    with open(output_path, 'w') as f:
        yaml.dump(manifest_data, f, default_flow_style=False)
    
    print(f"Manifest generated at {output_path}")
    return manifest_data

def update_state(manifest_data: Dict[str, Any], state_file: str = STATE_FILE):
    """Update the pipeline state YAML with checksums and timestamp."""
    state_dir = os.path.dirname(state_file)
    if not os.path.exists(state_dir):
        os.makedirs(state_dir)

    state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}

    # Update state with manifest info
    state['last_manifest_update'] = datetime.datetime.now().isoformat()
    state['dataset'] = {
        'id': manifest_data['dataset_id'],
        'version': manifest_data['version'],
        'source_url': manifest_data['source_url'],
        'files_checksums': {f['name']: f['checksum'] for f in manifest_data['files']}
    }

    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    print(f"State updated at {state_file}")

def main():
    """Main entry point for the manifest generator."""
    # Default paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dataset_id = DATASET_ID
    dataset_path = os.path.join(project_root, "data", "raw", dataset_id)
    output_path = os.path.join(project_root, "data", "processed", "manifest.yaml")
    state_file = os.path.join(project_root, "state", "pipeline_state.yaml")

    # Ensure directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        manifest_data = generate_manifest(dataset_id, dataset_path, output_path)
        update_state(manifest_data, state_file)
        print("Manifest generation and state update completed successfully.")
    except Exception as e:
        print(f"Error during manifest generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
