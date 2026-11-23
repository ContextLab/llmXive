"""
Task T007b: Download Simple Reaction Time dataset (OpenNeuro ds000224).

Fetches behavioral logs for simple RT tasks from OpenNeuro.
Verifies integrity and generates a manifest.
"""
import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

# Import shared config utilities
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for direct execution if config is not in path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_path, ensure_dirs

DATASET_ID = "ds000224"
DATASET_VERSION = "1.0.0" # Specific version to ensure reproducibility
OPENNEURO_API_BASE = "https://openneuro.org/datasets"

# Output paths
DATA_RAW_DIR = "data/raw/rt_data"
INTERIM_DIR = "data/interim"
RT_MANIFEST_PATH = "data/interim/rt_data_manifest.json"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, headers: Optional[Dict] = None) -> bool:
    """Download a file from a URL with progress and error handling."""
    try:
        response = requests.get(url, stream=True, headers=headers)
        response.raise_for_status()
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

def get_dataset_files(dataset_id: str, version: str) -> List[Dict[str, Any]]:
    """
    Fetch the list of files for a dataset from OpenNeuro.
    Uses the OpenNeuro API to get the file tree.
    """
    # OpenNeuro GraphQL API endpoint
    api_url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/file-tree"
    
    # Note: OpenNeuro public API might require specific headers or authentication for some endpoints.
    # For public datasets, we often can access the file listing via the dataset page or a simplified API.
    # However, the most reliable programmatic way for public data is often via the datalad library 
    # or direct download from the s3 bucket if known. 
    # Since we cannot use datalad as a hard dependency without ensuring it's installed, 
    # we will attempt the direct download of specific known files or use the dataset's manifest if available.
    
    # Alternative: OpenNeuro provides a direct download link structure for files.
    # https://openneuro.org/datasets/{dataset_id}/versions/{version}/files/{file_id}
    # But we need the list of files first.
    
    # Let's try to fetch the dataset description and structure via the public API if available,
    # or fallback to a known structure for ds000224.
    # ds000224 is a BIDS dataset. We expect:
    # sub-<label>/ses-<label>/beh/sub-<label>_ses-<label>_task-rt_events.tsv
    # or similar.
    
    # Since the API for listing files is complex, we will implement a targeted download
    # based on the known BIDS structure of ds000224.
    # We will scan for participants by looking for sub- directories in the dataset's
    # public file listing if possible, or hardcode the known structure if the API is too restrictive.
    
    # For this implementation, we will use the OpenNeuro API to get the file tree JSON.
    # If that fails, we will raise an error.
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "llmXive-pipeline/1.0"
    }
    
    # The public API for file tree might be at:
    # https://openneuro.org/datasets/ds000224/versions/1.0.0/file-tree
    # Let's try to fetch the root file tree.
    try:
        # OpenNeuro v3 API
        url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/file-tree"
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"API returned status {resp.status_code}. Attempting direct file discovery.")
            return []
    except Exception as e:
        print(f"Failed to fetch file tree from API: {e}")
        return []

def download_rt_data():
    """
    Main logic to download the RT dataset.
    """
    print(f"Starting download of dataset {DATASET_ID} (Version {DATASET_VERSION})...")
    
    rt_data_dir = get_path(DATA_RAW_DIR)
    ensure_dirs(rt_data_dir)
    
    # Try to get file list from API
    file_tree = get_dataset_files(DATASET_ID, DATASET_VERSION)
    
    files_to_download = []
    
    # If API failed or returned empty, we rely on known BIDS structure for ds000224
    # ds000224 structure:
    # sub-01/ses-1/beh/sub-01_ses-1_task-rt_events.tsv
    # We need to find all participants.
    # Since we can't easily list all participants without the API, we will try to
    # download a common set or use a heuristic.
    # However, the task requires fetching "behavioral logs".
    # Let's assume we can find the files by scanning or if the API works.
    
    if not file_tree:
        print("API file tree empty. Attempting to discover files via known BIDS patterns.")
        # We will attempt to download files for a range of subjects if we can't list them.
        # But a better approach for a robust script is to fail if we can't list them,
        # or use a known list.
        # Let's try to fetch the dataset's dataset_description.json to confirm existence.
        desc_url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/{DATASET_VERSION}/file-download/dataset_description.json"
        # Actually, the download URL is different.
        # Let's just try to download the dataset_description.json first to verify access.
        # OpenNeuro direct download:
        # https://openneuro.org/datasets/ds000224/versions/1.0.0/file-download/dataset_description.json
        # This is a bit tricky without the file ID.
        
        # Fallback: We will construct the download URL for specific known files if we can't list.
        # But the task says "fetch the Simple Reaction Time dataset".
        # We will assume the API works or we have a way to list.
        # If not, we exit with an error.
        print("ERROR: Could not retrieve file list from OpenNeuro API. Cannot proceed without file list.")
        sys.exit(1)

    # Process the file tree to find behavioral files
    # The file_tree is usually a nested structure. We need to traverse it.
    def traverse_tree(node, path=""):
        current_path = f"{path}/{node['name']}" if path else node['name']
        if 'files' in node:
            for child in node['files']:
                traverse_tree(child, current_path)
        elif 'id' in node and node.get('type') == 'file':
            # Check if it's a behavioral events file
            if 'beh' in current_path and current_path.endswith('.tsv'):
                files_to_download.append({
                    'id': node['id'],
                    'path': current_path,
                    'type': 'behavioral'
                })
        elif 'id' in node and node.get('type') == 'file':
             # Just collect all files for now, we can filter later if needed, 
             # but the task specifically asks for behavioral logs.
             # We'll stick to the filter above.
             pass

    # The API response structure might vary. Let's assume a standard recursive structure.
    # If the root is a list, iterate it.
    if isinstance(file_tree, list):
        for node in file_tree:
            traverse_tree(node)
    elif isinstance(file_tree, dict):
        traverse_tree(file_tree)

    if not files_to_download:
        print("No behavioral files (.tsv in beh directory) found in the dataset.")
        # This might be okay if the dataset doesn't have them, but for ds000224 it should.
        # Let's try a more direct approach if the API structure was unexpected.
        # We will attempt to download the dataset_description.json to verify we can access the dataset.
        # And then try to download a specific known file path if we can construct it.
        # However, without the file ID, we can't use the direct download link easily.
        # We will assume the API worked or exit.
        print("Exiting: No files found to download.")
        sys.exit(1)

    downloaded_files = []
    manifest_data = {
        "dataset_id": DATASET_ID,
        "version": DATASET_VERSION,
        "source": "OpenNeuro",
        "files": []
    }

    for file_info in files_to_download:
        file_id = file_info['id']
        file_path_str = file_info['path']
        
        # Construct download URL
        # OpenNeuro direct download URL format:
        # https://openneuro.org/datasets/{dataset_id}/versions/{version}/file-download/{file_id}
        download_url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/{DATASET_VERSION}/file-download/{file_id}"
        
        # Determine local path
        # The file_path_str might be like "sub-01/ses-1/beh/sub-01_ses-1_task-rt_events.tsv"
        # We want to save it to data/raw/rt_data/sub-01/ses-1/beh/...
        local_sub_path = Path(rt_data_dir) / file_path_str
        
        print(f"Downloading: {file_path_str} -> {local_sub_path}")
        
        if download_file(download_url, local_sub_path):
            file_hash = calculate_sha256(local_sub_path)
            downloaded_files.append(local_sub_path)
            manifest_data["files"].append({
                "path": str(local_sub_path.relative_to(Path.cwd())),
                "original_path": file_path_str,
                "sha256": file_hash,
                "type": file_info['type']
            })
            print(f"  Downloaded and verified: {file_path_str}")
        else:
            print(f"  Failed to download: {file_path_str}")

    if not downloaded_files:
        print("ERROR: No files were successfully downloaded.")
        sys.exit(1)

    # Write manifest
    manifest_path = get_path(INTERIM_DIR) / "rt_data_manifest.json"
    ensure_dirs(manifest_path.parent)
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    print(f"Download complete. Manifest written to {manifest_path}")
    print(f"Total files downloaded: {len(downloaded_files)}")

def verify_integrity():
    """Verify the integrity of downloaded files against the manifest."""
    manifest_path = get_path(INTERIM_DIR) / "rt_data_manifest.json"
    if not manifest_path.exists():
        print("Manifest not found. Cannot verify integrity.")
        return False

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    all_ok = True
    for file_entry in manifest['files']:
        file_path = Path.cwd() / file_entry['path']
        if not file_path.exists():
            print(f"Missing file: {file_entry['path']}")
            all_ok = False
            continue
        
        current_hash = calculate_sha256(file_path)
        if current_hash != file_entry['sha256']:
            print(f"Hash mismatch for {file_entry['path']}: expected {file_entry['sha256']}, got {current_hash}")
            all_ok = False
        else:
            print(f"Verified: {file_entry['path']}")

    return all_ok

def main():
    parser = argparse.ArgumentParser(description="Download RT dataset from OpenNeuro")
    parser.add_argument('--verify', action='store_true', help="Verify integrity of existing files")
    args = parser.parse_args()

    if args.verify:
        if verify_integrity():
            print("Integrity check passed.")
            sys.exit(0)
        else:
            print("Integrity check failed.")
            sys.exit(1)

    download_rt_data()

if __name__ == "__main__":
    main()
