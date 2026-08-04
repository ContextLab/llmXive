import os
import subprocess
import time
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config_loader import get_project_root, get_config, ensure_directory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load project configuration from code/config.yaml."""
    return get_config()

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_manifest_hash(dataset_id: str, filename: str, manifest_path: Path) -> Optional[str]:
    """
    Extract the expected SHA256 hash for a specific file from the OpenNeuro manifest.
    The manifest is typically a JSON file containing an array of objects with 'filename' and 'checksum'.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return None

    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)

    for entry in manifest_data:
        if entry.get('filename') == filename:
            # OpenNeuro manifests often use 'checksum' or 'sha256'
            return entry.get('checksum') or entry.get('sha256')
    
    logger.warning(f"Hash not found for {filename} in manifest")
    return None

def download_file(url: str, dest_path: Path, retries: int = 3, backoff: int = 10) -> bool:
    """
    Download a file from a URL with retry logic.
    Uses wget via subprocess for robustness.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(1, retries + 1):
        logger.info(f"Downloading {url} (Attempt {attempt}/{retries})...")
        try:
            # Use wget with -O for output file and --show-progress
            # -q for quiet (unless error) is often better for logs, but let's be verbose
            result = subprocess.run(
                ['wget', '-O', str(dest_path), url],
                check=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info(f"Successfully downloaded: {dest_path}")
                return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Download failed: {e.stderr}")
        
        if attempt < retries:
            logger.info(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff
        else:
            logger.error(f"Failed to download {url} after {retries} attempts.")
            return False
    
    return False

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the SHA256 checksum of a downloaded file against the expected hash.
    Raises an error if they do not match.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for verification: {file_path}")
    
    logger.info(f"Verifying checksum for {file_path}...")
    actual_hash = calculate_sha256(file_path)
    
    if actual_hash.lower() == expected_hash.lower():
        logger.info(f"Checksum verification PASSED for {file_path}")
        return True
    else:
        error_msg = (
            f"Checksum verification FAILED for {file_path}. "
            f"Expected: {expected_hash}, Got: {actual_hash}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

def extract_tar_gz(tar_path: Path, dest_dir: Path) -> None:
    """Extract a .tar.gz file to the destination directory."""
    if not tar_path.exists():
        raise FileNotFoundError(f"Archive not found: {tar_path}")
    
    logger.info(f"Extracting {tar_path} to {dest_dir}...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(tar_path), str(dest_dir), format='gztar')
    logger.info("Extraction complete.")

def run_download_pipeline(dataset_id: str, target_dir: Path) -> None:
    """
    Main pipeline to download and verify the dataset.
    This function assumes T010 has handled the bulk download or will be called
    in a sequence where download happens first.
    For T011, we focus on the verification logic against the manifest.
    
    However, to make this a runnable script for T011 as described:
    "Verify checksums against OpenNeuro manifest hashes before finalizing data/raw"
    
    We will:
    1. Locate the manifest in data/raw (or download it if missing).
    2. Iterate over expected files.
    3. Verify checksums.
    """
    # Ensure target directory exists
    ensure_directory(target_dir)
    
    # OpenNeuro dataset manifest URL pattern
    # Usually: https://openneuro.org/datasets/{dataset_id}/file-display/ds{dataset_id}_version:1.0.0:dataset_description.json
    # But for file checksums, we need the 'md5' or 'sha256' manifest.
    # OpenNeuro provides a 'md5sums' or similar file, or we can use the API.
    # For this pipeline, we assume a 'manifest.json' or 'checksums.txt' exists or is downloaded.
    
    # Standard OpenNeuro checksums file is often at:
    # https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-display/checksums.txt
    # Or we download the dataset_description and derive.
    # Let's assume the manifest is available at a standard location or we fetch it.
    
    # For ds003645 (Auditory Oddball), the checksums are typically in a 'checksums.txt' or similar.
    # We will try to fetch the manifest from OpenNeuro's CDN if not present.
    
    manifest_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-display/checksums.txt"
    manifest_path = target_dir / "checksums.txt"
    
    if not manifest_path.exists():
        logger.info("Manifest not found locally, attempting to download...")
        if not download_file(manifest_url, manifest_path):
            raise RuntimeError("Failed to download manifest file. Cannot verify checksums.")
    
    # Parse manifest
    # Format usually: <hash>  <filename>
    expected_files = {}
    with open(manifest_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                # Handle potential multiple spaces
                hash_val = parts[0]
                fname = ' '.join(parts[1:])
                expected_files[fname] = hash_val
    
    logger.info(f"Found {len(expected_files)} files to verify in manifest.")
    
    verification_failed = False
    
    for filename, expected_hash in expected_files.items():
        file_path = target_dir / filename
        
        # Handle nested paths in manifest (e.g., sub-01/eeg/sub-01_task-auditory_eeg.json)
        if not file_path.exists():
            # Check if it's a nested path
            # Sometimes manifests list relative paths from the dataset root
            # We need to check if the file exists in the target_dir
            if not file_path.exists():
                logger.warning(f"File not found for verification: {file_path}")
                # Depending on strictness, this might be a failure or just a warning
                # For T011, we want to ensure integrity, so missing files are critical
                verification_failed = True
                continue
        
        try:
            verify_checksum(file_path, expected_hash)
        except ValueError as e:
            logger.error(str(e))
            verification_failed = True
        except Exception as e:
            logger.error(f"Unexpected error verifying {filename}: {e}")
            verification_failed = True
    
    if verification_failed:
        raise RuntimeError("Checksum verification failed for one or more files. Data integrity compromised.")
    
    logger.info("All checksums verified successfully. Data ready for processing.")

def download_openneuro_dataset(dataset_id: str, output_dir: Path) -> None:
    """
    Wrapper to orchestrate the full download and verification.
    T010 handles the bulk download (wget/curl), T011 handles verification.
    This function ensures both happen.
    """
    # 1. Download (Simulating T010 logic here for completeness if called standalone)
    # In the actual pipeline, T010 might have already done this. 
    # But for a complete script, we ensure data exists.
    
    # Construct download URL for the dataset (tar.gz)
    # OpenNeuro datasets can be downloaded via:
    # https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-download
    # Or via AWS S3.
    # For simplicity and robustness, we assume T010 has populated data/raw.
    # If not, we attempt a direct download of the dataset archive.
    
    # If data/raw is empty, we try to download the dataset.
    # This part is T010 logic, but we include it to make the script runnable.
    raw_dir = output_dir
    if not any(raw_dir.iterdir()):
        logger.warning("data/raw is empty. Attempting to download dataset (T010 logic)...")
        # We need a specific file to download for verification to work.
        # We will download the dataset_description.json first as a sanity check.
        desc_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-display/dataset_description.json"
        desc_path = raw_dir / "dataset_description.json"
        if download_file(desc_url, desc_path):
            logger.info("Dataset description downloaded. Proceeding to checksum verification.")
        else:
            raise RuntimeError("Could not download dataset to verify checksums.")
    
    # 2. Verify (T011 Logic)
    run_download_pipeline(dataset_id, output_dir)

def main():
    """Entry point for the download and verification script."""
    config = load_config()
    dataset_id = config.get('dataset_id', 'ds003645')
    raw_dir = get_project_root() / 'data' / 'raw'
    
    try:
        download_openneuro_dataset(dataset_id, raw_dir)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
