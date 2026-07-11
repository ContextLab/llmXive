"""
Codeforces Dataset Download and Verification Script.

This script verifies the availability of the Codeforces dataset,
downloads it, and captures version metadata (commit hash/API snapshot).

The Codeforces API problems dataset is hosted on GitHub via the 
'codeforces-api' repository or similar mirrors. We target the 
'problems.json' dataset which contains problem metadata and solution 
statistics.

Source: https://github.com/ajahuang/Codeforces-Data (or similar stable mirror)
Target: data/codeforces/problems.json
"""
import os
import sys
import json
import hashlib
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "codeforces"
OUTPUT_FILE = DATA_DIR / "problems.json"
METADATA_FILE = DATA_DIR / "metadata.json"

# Configuration
# Using a stable mirror for Codeforces problems data.
# Note: In a real production environment, this would point to a 
# specific commit tag of a dataset repository to ensure reproducibility.
# Current target: The 'problems.json' from the popular 'ajahuang/Codeforces-Data' repo
# which is a snapshot of Codeforces problems.
DATA_URL = "https://raw.githubusercontent.com/ajahuang/Codeforces-Data/master/problems.json"
COMMIT_REF = "master"  # In production, replace with a specific SHA for reproducibility
EXPECTED_MIN_SIZE = 100000  # Bytes, sanity check

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Download a file from URL to dest_path.
    Returns (success, error_message).
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"Downloading {url} to {dest_path}...")
        with urllib.request.urlopen(url, timeout=60) as response:
            if response.status != 200:
                return False, f"HTTP Status {response.status}"
            
            with open(dest_path, 'wb') as out_file:
                content_length = 0
                while True:
                    chunk = response.read(4096)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    content_length += len(chunk)
            
            if content_length < EXPECTED_MIN_SIZE:
                return False, f"File too small: {content_length} bytes"
            
            return True, None
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Download Error: {str(e)}"

def validate_json_structure(file_path: Path) -> bool:
    """Basic validation of JSON structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Check if it's a list or dict with expected keys
        if isinstance(data, list) and len(data) > 0:
            return True
        if isinstance(data, dict) and "problems" in data:
            return True
        return False
    except json.JSONDecodeError:
        return False

def save_metadata(file_path: Path, url: str, commit_ref: str, success: bool, error: Optional[str] = None):
    """Save download metadata to a JSON file."""
    metadata = {
        "dataset": "Codeforces Problems",
        "source_url": url,
        "commit_ref": commit_ref,
        "download_timestamp": datetime.utcnow().isoformat(),
        "success": success,
        "error": error,
        "file_hash": None,
        "file_size": None
    }
    
    if success and file_path.exists():
        metadata["file_hash"] = compute_file_hash(file_path)
        metadata["file_size"] = file_path.stat().st_size
        metadata["load_rate"] = "N/A" # Calculated later in problem loading phase

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    return metadata

def main():
    """Main entry point for the script."""
    print(f"Starting Codeforces dataset verification and download...")
    print(f"Target directory: {DATA_DIR}")
    
    # Ensure directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists and is valid (optional optimization)
    if OUTPUT_FILE.exists():
        if validate_json_structure(OUTPUT_FILE):
            print("Existing valid file found. Saving metadata only.")
            save_metadata(OUTPUT_FILE, DATA_URL, COMMIT_REF, True)
            return 0
        else:
            print("Existing file is invalid. Re-downloading...")
    
    # Download
    success, error = download_file(DATA_URL, OUTPUT_FILE)
    
    if not success:
        print(f"ERROR: Download failed. {error}")
        save_metadata(OUTPUT_FILE, DATA_URL, COMMIT_REF, False, error)
        return 1
    
    # Validate
    if not validate_json_structure(OUTPUT_FILE):
        print("ERROR: Downloaded file is not valid JSON or has unexpected structure.")
        save_metadata(OUTPUT_FILE, DATA_URL, COMMIT_REF, False, "Invalid JSON structure")
        return 1
    
    # Success
    print(f"Successfully downloaded and verified Codeforces dataset.")
    print(f"File: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size} bytes")
    print(f"Hash: {compute_file_hash(OUTPUT_FILE)}")
    
    save_metadata(OUTPUT_FILE, DATA_URL, COMMIT_REF, True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
