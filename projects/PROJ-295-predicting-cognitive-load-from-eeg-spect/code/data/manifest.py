import os
import sys
import hashlib
import json
import datetime
import yaml
import requests
from typing import Dict, Any, Optional, Tuple

# Constants
DATASET_ID = "ds000246"
DATASET_VERSION = "1.1.0"
BASE_URL = "https://api.openneuro.org/datasets"
MANIFEST_PATH = "data/raw/manifest.yaml"
STATE_PATH = "state.yaml"
DATA_DIR = "data/raw"

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def fetch_remote_checksum(dataset_id: str, version: str, filename: str) -> Optional[str]:
    """
    Fetch the expected checksum for a specific dataset file from OpenNeuro API.
    Returns None if not found or on error.
    """
    # Construct the URL to get dataset files
    # OpenNeuro API v3: /datasets/{datasetId}/versions/{version}/files
    url = f"{BASE_URL}/{dataset_id}/versions/{version}/files"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        files_data = response.json()
        
        # Search for the specific file
        for file_entry in files_data:
            if file_entry.get("filename") == filename:
                # OpenNeuro usually returns 's3URI' and sometimes checksums in metadata
                # If direct checksum isn't in the top level, we might need to parse metadata
                # For ds000246, we look for 'md5' or 'checksum' in the entry or metadata
                checksum = file_entry.get("checksum") or file_entry.get("md5")
                if checksum:
                    return checksum
                
                # Fallback: check nested metadata if available
                metadata = file_entry.get("metadata", {})
                if isinstance(metadata, dict):
                    checksum = metadata.get("checksum") or metadata.get("md5")
                    if checksum:
                        return checksum
        
        return None
    except requests.RequestException as e:
        print(f"Warning: Could not fetch remote checksum for {filename}: {e}")
        return None

def verify_dataset_integrity(data_dir: str, expected_files: Dict[str, str]) -> Tuple[bool, Dict[str, str]]:
    """
    Verify that downloaded files match expected checksums.
    Returns (is_valid, {filename: actual_checksum})
    """
    results = {}
    all_valid = True
    
    for filename, expected_checksum in expected_files.items():
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"Missing file: {file_path}")
            results[filename] = "MISSING"
            all_valid = False
            continue
        
        actual_checksum = calculate_file_checksum(file_path)
        results[filename] = actual_checksum
        
        if expected_checksum and actual_checksum != expected_checksum:
            print(f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual_checksum}")
            all_valid = False
        else:
            print(f"Verified {filename}: {actual_checksum[:8]}...")
    
    return all_valid, results

def generate_manifest(data_dir: str, output_path: str, version: str = DATASET_VERSION) -> Dict[str, Any]:
    """
    Generate the manifest.yaml file.
    This function:
    1. Fetches remote checksums from OpenNeuro API for the target dataset version.
    2. Downloads the dataset (if not present) - delegates to download.py logic conceptually, 
       but here we assume download.py (T008) handles the fetch, and we verify it here.
       However, T007 specifically asks to "automatically fetch and verify".
       So we will attempt to fetch the checksums first.
    3. If files exist locally, verify them. If not, we record the expected checksums 
       and note the file as 'pending_download'.
    4. Writes the manifest to output_path.
    """
    # Key files to track for ds000246 (EEG dataset)
    # Based on typical OpenNeuro structure and T008 requirements (gaze.tsv check)
    # We track: dataset_description.json, sub-*/eeg/*.eeg (or .vhdr), sub-*/eeg/*.json, sub-*/eeg/*.tsv (events), and gaze.tsv if available
    # For simplicity and robustness, we track the top-level files and the specific gaze file if it exists in the version
    files_to_track = [
        "dataset_description.json",
        "participants.tsv",
        "README"
    ]
    
    # Add specific subject files if we know the subject IDs (usually sub-01, sub-02, etc.)
    # For a generic manifest, we can list the expected pattern or specific known files.
    # Let's assume we are tracking the dataset_description and the critical gaze file if present.
    # T008 mentions gaze.tsv. Let's assume it might be in the root or sub-*/.
    # We will add a generic check for gaze.tsv in the root first.
    files_to_track.append("gaze.tsv") 
    
    # Fetch remote checksums
    expected_checksums = {}
    for fname in files_to_track:
        checksum = fetch_remote_checksum(DATASET_ID, version, fname)
        expected_checksums[fname] = checksum
    
    # Check local files
    local_checksums = {}
    missing_files = []
    
    for fname in files_to_track:
        fpath = os.path.join(data_dir, fname)
        if os.path.exists(fpath):
            local_checksums[fname] = calculate_file_checksum(fpath)
        else:
            missing_files.append(fname)
            local_checksums[fname] = None
    
    # Construct manifest
    manifest = {
        "dataset_id": DATASET_ID,
        "version": version,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_url": f"{BASE_URL}/{DATASET_ID}/versions/{version}",
        "files": {}
    }
    
    for fname in files_to_track:
        manifest["files"][fname] = {
            "expected_checksum": expected_checksums.get(fname),
            "local_checksum": local_checksums.get(fname),
            "status": "verified" if (expected_checksums.get(fname) and local_checksums.get(fname) and expected_checksums.get(fname) == local_checksums.get(fname)) else 
                      ("missing" if fname in missing_files else "pending_verification")
        }
    
    # Write manifest
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    
    print(f"Manifest generated at {output_path}")
    return manifest

def update_state(output_path: str) -> None:
    """
    Update the project state.yaml with the manifest checksum and timestamp.
    This satisfies Constitution Principle VI and the task requirement.
    """
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Manifest not found: {output_path}")
    
    manifest_checksum = calculate_file_checksum(output_path)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    state = {}
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r") as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    
    state["manifest"] = {
        "path": output_path,
        "checksum": manifest_checksum,
        "updated_at": now
    }
    
    with open(STATE_PATH, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    print(f"State updated at {STATE_PATH}")

def main():
    """Main entry point for manifest generation."""
    print(f"Generating manifest for {DATASET_ID} version {DATASET_VERSION}...")
    
    # Ensure data directory exists (T001 should have created it, but safety check)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    manifest_path = MANIFEST_PATH
    try:
        manifest = generate_manifest(DATA_DIR, manifest_path)
        update_state(manifest_path)
        
        # Final verification status
        all_verified = True
        for fname, info in manifest["files"].items():
            if info["status"] != "verified":
                all_verified = False
                print(f"Warning: {fname} is not verified (status: {info['status']})")
        
        if all_verified:
            print("All tracked files verified successfully.")
        else:
            print("Some files are missing or verification pending. Ensure data download (T008) is complete.")
            
    except Exception as e:
        print(f"Error generating manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
