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
# Target: The 'problems.json' from the popular 'ajahuang/Codeforces-Data' repo
# which is a snapshot of Codeforces problems.
DATA_URL = "https://raw.githubusercontent.com/ajahuang/Codeforces-Data/master/problems.json"
# In production, replace with a specific SHA for reproducibility.
# We attempt to fetch the commit hash from the GitHub API.
GITHUB_API_URL = "https://api.github.com/repos/ajahuang/Codeforces-Data/commits?path=problems.json&sha=master&per_page=1"
COMMIT_REF = "master"
EXPECTED_MIN_SIZE = 100000  # Bytes, sanity check

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_commit_hash() -> Optional[str]:
    """
    Fetch the latest commit hash for the target file from GitHub API.
    Returns None if the request fails.
    """
    try:
        req = urllib.request.Request(GITHUB_API_URL, headers={"User-Agent": "llmXive-research"})
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if isinstance(data, list) and len(data) > 0:
                    sha = data[0].get("sha")
                    if sha:
                        print(f"Captured commit hash: {sha}")
                        return sha
    except Exception as e:
        print(f"Warning: Could not fetch commit hash from GitHub API: {e}")
    return None

def download_file(url: str, dest_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Download a file from URL to dest_path.
    Returns (success, error_message).
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        print(f"Downloading {url} to {dest_path}...")
        with urllib.request.urlopen(url, timeout=120) as response:
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
        "file_size": None,
        "load_rate": "N/A"  # Calculated later in problem loading phase
    }

    if success and file_path.exists():
        metadata["file_hash"] = compute_file_hash(file_path)
        metadata["file_size"] = file_path.stat().st_size

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    return metadata

def main():
    """Main entry point for the script."""
    print(f"Starting Codeforces dataset verification and download...")
    print(f"Target directory: {DATA_DIR}")

    # Ensure directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Attempt to fetch the real commit hash from GitHub API
    commit_hash = fetch_commit_hash()
    if commit_hash:
        print(f"Using commit hash: {commit_hash}")
        # We use the specific hash in the metadata for reproducibility
        # even if we download from the 'master' branch URL (which is stable).
        # In a fully reproducible pipeline, we would download the specific blob.
        effective_commit_ref = commit_hash
    else:
        print("Warning: Could not fetch commit hash. Using branch name.")
        effective_commit_ref = COMMIT_REF

    # Check if file already exists and is valid (optional optimization)
    if OUTPUT_FILE.exists():
        if validate_json_structure(OUTPUT_FILE):
            print("Existing valid file found. Saving metadata only.")
            save_metadata(OUTPUT_FILE, DATA_URL, effective_commit_ref, True)
            return 0
        else:
            print("Existing file is invalid. Re-downloading...")

    # Download
    success, error = download_file(DATA_URL, OUTPUT_FILE)

    if not success:
        print(f"ERROR: Download failed. {error}")
        save_metadata(OUTPUT_FILE, DATA_URL, effective_commit_ref, False, error)
        return 1

    # Validate
    if not validate_json_structure(OUTPUT_FILE):
        print("ERROR: Downloaded file is not valid JSON or has unexpected structure.")
        save_metadata(OUTPUT_FILE, DATA_URL, effective_commit_ref, False, "Invalid JSON structure")
        return 1

    # Success
    print(f"Successfully downloaded and verified Codeforces dataset.")
    print(f"File: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size} bytes")
    print(f"Hash: {compute_file_hash(OUTPUT_FILE)}")
    print(f"Commit Hash: {effective_commit_ref}")

    save_metadata(OUTPUT_FILE, DATA_URL, effective_commit_ref, True)
    return 0

if __name__ == "__main__":
    sys.exit(main())