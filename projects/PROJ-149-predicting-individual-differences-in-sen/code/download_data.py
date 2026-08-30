"""
Download and verify the PhysioNet EEG Motor Movement/Imagery Dataset (Dataset ID: 100).

This script fetches raw EDF files, verifies cryptographic checksums against the
manifest provided by PhysioNet, and generates a local manifest for downstream tasks.

Dependencies:
    - physionet (pip install physionet)
    - requests (for manifest fetching if not via package)
    - hashlib (standard library)

Output:
    - data/raw/eegmmidb/ (raw EDF files)
    - data/interim/data_source_manifest.json (file paths and verified hashes)
"""
import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path to ensure imports work if run as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import physionet
except ImportError:
    print("Error: The 'physionet' package is required. Install it via: pip install physionet")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: The 'requests' package is required. Install it via: pip install requests")
    sys.exit(1)

from config import get_path, ensure_dirs

# Constants
DATASET_ID = "100"
DATASET_NAME = "eegmmidb"
PHYSIONET_BASE_URL = "https://physionet.org/files/eegmmidb/1.0.0/"
MANIFEST_URL = f"{PHYSIONET_BASE_URL}MANIFEST.md5" # PhysioNet typically uses .md5 or .md5sum

# Local paths
RAW_DATA_DIR = project_root / "data" / "raw" / DATASET_NAME
INTERIM_DIR = project_root / "data" / "interim"
MANIFEST_OUTPUT_PATH = INTERIM_DIR / "data_source_manifest.json"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_dataset():
    """
    Download the dataset using the physionet package.
    Falls back to manual download if the package API is limited for specific checksums.
    """
    print(f"Starting download for Dataset ID: {DATASET_ID} ({DATASET_NAME})...")
    
    # Ensure directories exist
    ensure_dirs(RAW_DATA_DIR)
    ensure_dirs(INTERIM_DIR)

    # Check if data already exists to avoid re-downloading
    if RAW_DATA_DIR.exists() and any(RAW_DATA_DIR.glob("*.edf")):
        print(f"Data directory {RAW_DATA_DIR} already contains files. Skipping download.")
        # We still need to verify integrity in the next step, so we return True
        return True

    try:
        # Attempt to use physionet package
        # The physionet package usually handles downloading.
        # We target the specific version 1.0.0
        print(f"Fetching dataset {DATASET_ID} version 1.0.0 from PhysioNet...")
        
        # Note: The physionet package might not expose a direct 'download' function 
        # that returns file paths easily in all versions. We will use the standard 
        # download mechanism provided by the package or fallback to requests if needed.
        # However, based on standard physionet package usage:
        
        # If the package has a CLI or specific download function, we use it.
        # Since we cannot rely on the internal API of 'physionet' without documentation,
        # we will use a robust fallback to 'requests' to fetch the files listed in the manifest,
        # ensuring we have the exact files we need to verify.
        
        # First, fetch the manifest to know what to download
        manifest_resp = requests.get(MANIFEST_URL)
        if manifest_resp.status_code != 200:
            # Try alternative manifest name
            manifest_resp = requests.get(f"{PHYSIONET_BASE_URL}MANIFEST.md5sum")
        
        if manifest_resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch manifest from {MANIFEST_URL}. Status: {manifest_resp.status_code}")

        manifest_content = manifest_resp.text
        
        # Parse manifest (format: hash  filename)
        files_to_download = {}
        for line in manifest_content.splitlines():
            if line.strip() and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 2:
                    # PhysioNet manifests often use MD5
                    hash_val = parts[0]
                    filename = parts[1].strip()
                    if filename.endswith(".edf") or filename.endswith(".vhdr") or filename.endswith(".eeg"):
                        files_to_download[filename] = hash_val

        if not files_to_download:
            raise RuntimeError("No valid EDF/EEG files found in the manifest.")

        print(f"Found {len(files_to_download)} files to download.")

        for filename, expected_md5 in files_to_download.items():
            file_url = f"{PHYSIONET_BASE_URL}{filename}"
            local_path = RAW_DATA_DIR / filename
            
            if local_path.exists():
                # Verify existing file
                current_md5 = hashlib.md5(local_path.open('rb').read()).hexdigest()
                if current_md5 == expected_md5:
                    print(f"  [SKIP] {filename} (verified)")
                    continue
                else:
                    print(f"  [CORRUPT] {filename} (hash mismatch, re-downloading)")
            
            print(f"  [DOWNLOAD] {filename}")
            resp = requests.get(file_url, stream=True)
            if resp.status_code != 200:
                print(f"    Error: Failed to download {filename}. Status: {resp.status_code}")
                continue
            
            with open(local_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify immediately
            current_md5 = hashlib.md5(local_path.open('rb').read()).hexdigest()
            if current_md5 != expected_md5:
                print(f"    Error: Checksum verification failed for {filename}.")
                os.remove(local_path)
                continue
            
            print(f"    [OK] {filename} (MD5 verified)")

        return True

    except Exception as e:
        print(f"Error during download: {e}")
        return False

def verify_integrity():
    """
    Verify all downloaded files against the manifest checksums.
    Returns a list of verified files and their hashes.
    """
    print("Verifying integrity of downloaded files...")
    verified_files = []
    
    # Fetch manifest again for verification
    try:
        manifest_resp = requests.get(MANIFEST_URL)
        if manifest_resp.status_code != 200:
            manifest_resp = requests.get(f"{PHYSIONET_BASE_URL}MANIFEST.md5sum")
        manifest_resp.raise_for_status()
        manifest_content = manifest_resp.text
    except Exception as e:
        print(f"Error fetching manifest for verification: {e}")
        return False, []

    # Parse manifest
    expected_hashes = {}
    for line in manifest_content.splitlines():
        if line.strip() and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                filename = parts[1].strip()
                expected_hashes[filename] = parts[0]

    all_verified = True
    for filename, expected_hash in expected_hashes.items():
        local_path = RAW_DATA_DIR / filename
        if not local_path.exists():
            print(f"  [MISSING] {filename}")
            all_verified = False
            continue

        # PhysioNet uses MD5 in the manifest
        calculated_md5 = hashlib.md5(local_path.open('rb').read()).hexdigest()
        
        if calculated_md5 == expected_hash:
            verified_files.append({
                "filename": filename,
                "path": str(local_path),
                "md5": calculated_md5,
                "sha256": calculate_sha256(local_path),
                "verified": True
            })
        else:
            print(f"  [FAIL] {filename}: Expected {expected_hash}, Got {calculated_md5}")
            all_verified = False

    return all_verified, verified_files

def generate_manifest(verified_files: list):
    """
    Generate the JSON manifest for downstream tasks.
    """
    manifest_data = {
        "dataset_id": DATASET_ID,
        "dataset_name": DATASET_NAME,
        "version": "1.0.0",
        "source_url": PHYSIONET_BASE_URL,
        "generated_at": datetime.utcnow().isoformat(),
        "total_files": len(verified_files),
        "files": verified_files
    }
    
    with open(MANIFEST_OUTPUT_PATH, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    print(f"Manifest written to: {MANIFEST_OUTPUT_PATH}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Download and verify PhysioNet EEG Motor Movement/Imagery Dataset.")
    parser.add_argument("--check", action="store_true", help="Only check integrity of existing files.")
    args = parser.parse_args()

    # Ensure base directories exist
    ensure_dirs(RAW_DATA_DIR)
    ensure_dirs(INTERIM_DIR)

    if args.check:
        print("Running integrity check only...")
        success, verified = verify_integrity()
        if success:
            generate_manifest(verified)
            print("Integrity check passed.")
            sys.exit(0)
        else:
            print("Integrity check failed.")
            sys.exit(1)

    # Download
    if not download_dataset():
        print("Download failed.")
        sys.exit(1)

    # Verify
    success, verified = verify_integrity()
    if not success:
        print("Verification failed. Some files are missing or corrupted.")
        sys.exit(1)

    # Generate Manifest
    if not generate_manifest(verified):
        print("Failed to generate manifest.")
        sys.exit(1)

    print("Download and verification complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()
