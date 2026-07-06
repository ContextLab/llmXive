"""
Download module for ds000228.
Fetches NIfTI files for subjects listed in data/raw/valid_subjects.json.
"""
import json
import os
import sys
import time
import shutil
import tarfile
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

# Project imports
from utils.config import get_config_summary
from utils.memory_monitor import check_memory_limit, MemoryMonitor

# Constants
DATASET_ID = "ds000228"
OPENNEURO_BASE = "https://openneuro.org/datasets"
API_BASE = "https://api.openneuro.org"

# Output directory relative to project root
RAW_DATA_DIR = Path("data/raw")
VALID_SUBJECTS_FILE = RAW_DATA_DIR / "valid_subjects.json"
DOWNLOAD_LOG_FILE = RAW_DATA_DIR / "download_log.json"

def get_subject_urls(subject_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch download URLs for specific subjects from OpenNeuro API.
    Returns a list of dicts with subject_id and download_url.
    """
    # Construct the snapshot URL (using latest snapshot 'git-refs/heads/master' or similar)
    # OpenNeuro v3/v4 API structure
    dataset_url = f"{API_BASE}/datasets/{DATASET_ID}/snapshots"
    
    # We need to find the latest snapshot hash
    try:
        resp = requests.get(dataset_url, timeout=30)
        resp.raise_for_status()
        snapshots = resp.json()
        if not snapshots:
            raise RuntimeError(f"No snapshots found for {DATASET_ID}")
        
        # Sort by creation date to get the latest
        latest_snapshot = max(snapshots, key=lambda x: x.get('created', '0'))
        snapshot_id = latest_snapshot.get('id')
        
        if not snapshot_id:
            raise RuntimeError("Could not determine latest snapshot ID")
        
        # Construct subject download URLs
        # OpenNeuro API v4: /datasets/{dataset}/snapshots/{snapshot}/subjects/{subject}
        # But for direct download of derivatives or raw, we often use the s3 bucket or a specific endpoint.
        # However, the standard way for this task without S3 keys is to use the web API to get the tarball.
        # Actually, OpenNeuro provides a specific endpoint for subject downloads:
        # https://openneuro.org/datasets/{dataset}/versions/{version}/download
        # But that usually requires a CLI or specific permissions.
        
        # Alternative: Use the public s3 bucket if accessible without auth, or the API to get the manifest.
        # Given constraints, we will try to fetch the manifest of the latest snapshot.
        manifest_url = f"{API_BASE}/datasets/{DATASET_ID}/snapshots/{snapshot_id}/download"
        
        # If we can't get a direct tarball URL for subjects, we might need to parse the snapshot content.
        # Let's try to get the snapshot details which often includes the download link or we can construct it.
        # For ds000228, the data is often available via the standard structure.
        # We will construct the URL for the subject tarball if available, or fall back to the full dataset if needed.
        # However, the task asks for specific subjects.
        
        # Let's try the standard OpenNeuro API for subject files.
        # Actually, the most robust way without credentials is to download the full dataset and filter,
        # OR use the public S3 bucket if the dataset is public. ds000228 is public.
        # S3 URL pattern: s3://openneuro.org/ds000228/sub-{id}/...
        # We can use the `openneuro-py` package or construct the S3 URL directly if we assume public access.
        # Since we can't install heavy packages, let's try to fetch the subject list from the snapshot.
        
        # Re-evaluating: The OpenNeuro API v4 allows getting the snapshot.
        # We will assume we can download the subject tarballs if they exist, or we download the whole thing.
        # But the requirement is "fetch NIfTI files for subjects listed".
        # Let's try to construct the URL for the subject's functional data.
        
        # Fallback strategy for this specific task without S3 CLI:
        # 1. Get the latest snapshot.
        # 2. Try to get the download URL for that snapshot.
        # 3. If the API returns a tarball for the whole dataset, we might need to download and extract only specific subjects.
        #    However, downloading 50 subjects worth of data from a single tarball might be heavy.
        #    Let's check if we can get per-subject URLs.
        
        # Actually, for ds000228, the data is often in a specific structure.
        # Let's use the `requests` library to fetch the manifest of the snapshot.
        # If the API doesn't support per-subject tarballs directly, we will download the full dataset snapshot 
        # (if it fits) or the specific subject folders if the API supports it.
        
        # Given the "Real data" constraint and "No fabrication", we must fetch from the real source.
        # The most reliable programmatic way without credentials is the public S3 bucket.
        # URL: https://openneuro.org/datasets/ds000228/versions/1.0.0/download
        # Or direct S3: https://openneuro.s3.amazonaws.com/ds000228/sub-...
        
        # Let's try to get the snapshot version string.
        version = latest_snapshot.get('tag') or latest_snapshot.get('id')
        
        # Construct the base URL for the dataset version
        base_download_url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/{version}/download"
        
        # We will return a list of subjects and a strategy to fetch them.
        # Since we can't easily download partial tarballs from the main API without the CLI,
        # and S3 might be restricted or require specific permissions for partial access,
        # we will implement a strategy to download the full dataset snapshot if it's small enough,
        # OR attempt to download per-subject if the API allows.
        
        # For ds000228, the dataset is relatively small (fMRI resting state).
        # We will download the full snapshot tarball and then extract only the required subjects.
        # This ensures we get real data without needing complex S3 permissions.
        
        return {
            "snapshot_id": snapshot_id,
            "version": version,
            "download_url": base_download_url,
            "subject_ids": subject_ids
        }
        
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch snapshot metadata from OpenNeuro: {e}")

def download_and_extract_subjects(download_info: Dict[str, Any], output_dir: Path):
    """
    Downloads the dataset snapshot and extracts only the required subjects.
    """
    subject_ids = download_info["subject_ids"]
    download_url = download_info["download_url"]
    version = download_info["version"]
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a temporary file for the download
    temp_tarball = output_dir / f"{DATASET_ID}_{version}.tar.gz"
    
    print(f"Downloading dataset snapshot {version} from {download_url}...")
    print("(This may take a while depending on network speed)")
    
    try:
        # Stream the download
        with requests.get(download_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(temp_tarball, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    check_memory_limit() # Check memory periodically
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            sys.stdout.write(f"\rDownloaded: {percent:.1f}%")
                            sys.stdout.flush()
            sys.stdout.write("\nDownload complete.\n")
            
        # Extract only the required subjects
        print(f"Extracting subjects: {subject_ids}...")
        extracted_count = 0
        
        with tarfile.open(temp_tarball, 'r:gz') as tar:
            for member in tar.getmembers():
                # Check if this member belongs to one of our target subjects
                # Path format usually: ds000228/sub-XX/...
                parts = member.path.split(os.sep)
                if len(parts) > 0:
                    # Find sub-XX pattern
                    for part in parts:
                        if part.startswith("sub-"):
                            sub_id = part.split("-")[1] # e.g., "001"
                            if sub_id in subject_ids:
                                tar.extract(member, output_dir)
                                extracted_count += 1
                                break
        
        print(f"Extracted {extracted_count} files/directories for {len(subject_ids)} subjects.")
        
        # Clean up the tarball
        print("Cleaning up temporary tarball...")
        os.remove(temp_tarball)
        
        # Verify extraction
        for sub_id in subject_ids:
            sub_dir = output_dir / f"sub-{sub_id}"
            if not sub_dir.exists():
                print(f"Warning: Directory for sub-{sub_id} was not found after extraction.")
            else:
                # Check for NIfTI files
                nii_files = list(sub_dir.rglob("*.nii.gz"))
                if not nii_files:
                    print(f"Warning: No .nii.gz files found for sub-{sub_id}")
                else:
                    print(f"Found {len(nii_files)} NIfTI files for sub-{sub_id}")

    except Exception as e:
        # Clean up on failure
        if temp_tarball.exists():
            temp_tarball.unlink()
        raise RuntimeError(f"Failed to download or extract data: {e}")

def load_valid_subjects() -> List[str]:
    """
    Load the list of valid subject IDs from the filtered subjects file.
    """
    if not VALID_SUBJECTS_FILE.exists():
        raise FileNotFoundError(f"Valid subjects file not found: {VALID_SUBJECTS_FILE}")
    
    with open(VALID_SUBJECTS_FILE, 'r') as f:
        data = json.load(f)
    
    # Expected format: {"subjects": ["001", "002", ...]} or similar
    # Based on T015 output description: "generate data/raw/valid_subjects.json"
    # We assume it contains a list of subject IDs.
    if "subjects" in data:
        return data["subjects"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Invalid format in valid_subjects.json. Expected 'subjects' key or a list.")

def save_download_log(downloaded_subjects: List[str], success: bool, error: Optional[str] = None):
    """
    Save the download log.
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset": DATASET_ID,
        "requested_subjects": downloaded_subjects,
        "success": success,
        "error": error
    }
    
    with open(DOWNLOAD_LOG_FILE, 'w') as f:
        json.dump(log_entry, f, indent=2)

def main():
    """
    Main entry point for the download task.
    """
    print("Starting T016: Data Download for ds000228")
    
    # Check memory
    check_memory_limit()
    
    # Load valid subjects
    try:
        subject_ids = load_valid_subjects()
        print(f"Loaded {len(subject_ids)} subject IDs to download.")
    except Exception as e:
        print(f"Error loading valid subjects: {e}")
        save_download_log([], False, str(e))
        sys.exit(1)
    
    if not subject_ids:
        print("No subjects to download.")
        save_download_log([], True)
        sys.exit(0)
    
    # Get download URLs
    try:
        download_info = get_subject_urls(subject_ids)
    except Exception as e:
        print(f"Error fetching download info: {e}")
        save_download_log(subject_ids, False, str(e))
        sys.exit(1)
    
    # Download and extract
    try:
        download_and_extract_subjects(download_info, RAW_DATA_DIR)
        save_download_log(subject_ids, True)
        print("Download and extraction completed successfully.")
    except Exception as e:
        print(f"Error during download/extraction: {e}")
        save_download_log(subject_ids, False, str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
