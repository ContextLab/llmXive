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

def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """
    Extract a .zip or .tar.gz archive to the destination directory.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    logger.info(f"Extracting {archive_path} to {dest_dir}...")
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(archive_path), str(dest_dir))
    logger.info("Extraction complete.")

def download_dataset_archive(dataset_id: str, dest_dir: Path) -> Path:
    """
    Download the full OpenNeuro dataset archive (zip) for the given dataset_id.
    Returns the path to the downloaded archive.
    """
    archive_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/download"
    archive_path = dest_dir / f"{dataset_id}.zip"
    if archive_path.exists():
        logger.info(f"Archive already exists at {archive_path}, skipping download.")
        return archive_path

    logger.info(f"Attempting to download dataset archive from {archive_url}")
    success = download_file(archive_url, archive_path)
    if not success:
        raise RuntimeError(f"Failed to download dataset archive from {archive_url}")
    return archive_path

def run_download_pipeline(dataset_id: str, target_dir: Path) -> None:
    """
    Main pipeline to download and verify the dataset.
    This function first ensures the dataset archive is present,
    extracts it to the target directory, and then verifies checksums
    using the OpenNeuro manifest.
    """
    # Ensure target directory exists
    ensure_directory('raw_data')

    # Step 1: Download dataset archive if needed
    archive_path = download_dataset_archive(dataset_id, target_dir)

    # Step 2: Extract archive (if not already extracted)
    # Simple heuristic: if target_dir contains subdirectories like 'sub-01', assume extraction done.
    if not any((target_dir / d).is_dir() for d in os.listdir(target_dir) if d.startswith('sub-')):
        logger.info("Extracting dataset archive...")
        extract_archive(archive_path, target_dir)
    else:
        logger.info("Dataset appears already extracted; skipping extraction.")

    # Step 3: Verify checksums using manifest
    # Manifest URL pattern for OpenNeuro checksums (txt file with SHA256 hashes)
    manifest_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-display/checksums.txt"
    manifest_path = target_dir / "checksums.txt"

    if not manifest_path.exists():
        logger.info("Manifest not found locally, attempting to download...")
        if not download_file(manifest_url, manifest_path):
            raise RuntimeError("Failed to download manifest file. Cannot verify checksums.")

    # Parse manifest (format: <hash>  <relative_path>)
    expected_files = {}
    with open(manifest_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                hash_val = parts[0]
                fname = ' '.join(parts[1:])
                expected_files[fname] = hash_val

    logger.info(f"Found {len(expected_files)} entries in manifest for verification.")

    verification_failed = False
    for filename, expected_hash in expected_files.items():
        file_path = target_dir / filename
        if not file_path.exists():
            logger.error(f"Expected file missing for verification: {file_path}")
            verification_failed = True
            continue
        try:
            verify_checksum(file_path, expected_hash)
        except Exception as e:
            logger.error(str(e))
            verification_failed = True

    if verification_failed:
        raise RuntimeError("Checksum verification failed for one or more files. Data integrity compromised.")

    logger.info("All checksums verified successfully. Data ready for processing.")

def download_openneuro_dataset(dataset_id: str, output_dir: Path) -> None:
    """
    Wrapper to orchestrate the full download and verification.
    This function can be called directly from the CLI or imported by other scripts.
    """
    raw_dir = output_dir

    # If raw_dir already contains data, we assume download was previously successful.
    if any(raw_dir.iterdir()):
        logger.info(f"Data directory {raw_dir} already contains files. Skipping download step.")
    else:
        logger.info(f"Data directory {raw_dir} is empty. Proceeding with download.")

    # Perform download and verification pipeline
    run_download_pipeline(dataset_id, raw_dir)

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