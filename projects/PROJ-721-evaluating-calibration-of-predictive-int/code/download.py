"""
Download and validate the M4 dataset from the official GitHub repository.

This module handles fetching the M4-Dataset.zip and manifest.json files,
validating SHA256 checksums against the manifest, and extracting the data
to the project's data directory.
"""
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Configuration
REPO_OWNER = "M4-competition-org"
REPO_NAME = "M4-competition"
RELEASE_TAG = "v1.0"

# Files to download
ZIP_FILENAME = "M4-Dataset.zip"
MANIFEST_FILENAME = "manifest.json"

# URLs (constructed from GitHub release assets)
BASE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/{RELEASE_TAG}"
ZIP_URL = f"{BASE_URL}/{ZIP_FILENAME}"
MANIFEST_URL = f"{BASE_URL}/{MANIFEST_FILENAME}"

# Local paths
DATA_DIR = Path("data")
DOWNLOAD_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "m4"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: Path) -> Path:
    """Download a file from URL to destination."""
    print(f"Downloading {url}...")
    try:
        urlretrieve(url, destination)
        print(f"Successfully downloaded to {destination}")
        return destination
    except HTTPError as e:
        raise RuntimeError(f"HTTP error downloading {url}: {e.code} {e.reason}")
    except URLError as e:
        raise RuntimeError(f"URL error downloading {url}: {e.reason}")

def load_manifest(manifest_path: Path) -> dict:
    """Load and parse the manifest JSON file."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_checksums(manifest: dict, zip_path: Path) -> bool:
    """Validate SHA256 checksums from manifest against downloaded file."""
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")
    
    actual_hash = calculate_sha256(zip_path)
    expected_hash = manifest.get(ZIP_FILENAME, {}).get("sha256")
    
    if not expected_hash:
        raise ValueError(f"SHA256 hash for {ZIP_FILENAME} not found in manifest")
    
    print(f"Expected SHA256: {expected_hash}")
    print(f"Actual SHA256:   {actual_hash}")
    
    if actual_hash != expected_hash:
        raise ValueError(
            f"Checksum mismatch for {ZIP_FILENAME}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )
    
    print("✓ Checksum validation passed")
    return True

def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract zip file to destination directory."""
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")
    
    print(f"Extracting {zip_path} to {extract_to}...")
    extract_to.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    print(f"✓ Extraction complete: {extract_to}")

def cleanup_temp_files(zip_path: Path, manifest_path: Path) -> None:
    """Remove temporary download files after successful extraction."""
    if zip_path.exists():
        zip_path.unlink()
        print(f"Removed temporary zip file: {zip_path}")
    if manifest_path.exists():
        manifest_path.unlink()
        print(f"Removed temporary manifest file: {manifest_path}")

def main():
    """Main function to download, validate, and extract M4 dataset."""
    # Ensure directories exist
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    zip_path = DOWNLOAD_DIR / ZIP_FILENAME
    manifest_path = DOWNLOAD_DIR / MANIFEST_FILENAME
    
    try:
        # Download manifest first
        download_file(MANIFEST_URL, manifest_path)
        
        # Load manifest
        manifest = load_manifest(manifest_path)
        print("✓ Manifest loaded successfully")
        
        # Download dataset zip
        download_file(ZIP_URL, zip_path)
        
        # Validate checksums
        validate_checksums(manifest, zip_path)
        
        # Extract dataset
        extract_zip(zip_path, EXTRACTED_DIR)
        
        # Cleanup temporary files
        cleanup_temp_files(zip_path, manifest_path)
        
        print("\n✓ M4 dataset download and validation complete!")
        print(f"Data location: {EXTRACTED_DIR}")
        
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        print(f"\n✗ Error: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()