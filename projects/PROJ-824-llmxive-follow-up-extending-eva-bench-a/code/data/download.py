"""
Data download module for fetching EVA-Bench dataset.
Includes fail-fast error handling for download failures and corruption.
"""
import hashlib
import json
import os
import sys
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import error handling utilities
from data.error_handler import (
    DataCorruptionError,
    DownloadFailureError,
    verify_file_integrity,
    handle_download_failure
)
from config import DATA_DIR, DATASET_URL, DATASET_CHECKSUMS

# Configure logging
logger = logging.getLogger("llmxive.download")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load existing checksums from a JSON file."""
    if not checksum_file.exists():
        return {}
    try:
        with open(checksum_file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksum file {checksum_file}: {e}")
        return {}

def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """Save checksums to a JSON file."""
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)

def verify_downloaded_files(download_dir: Path, checksums: Dict[str, str]) -> List[str]:
    """
    Verifies all downloaded files against their checksums.
    Returns a list of files with mismatches (empty if all pass).
    """
    mismatches = []
    for filename, expected_hash in checksums.items():
        file_path = download_dir / filename
        if not file_path.exists():
            logger.warning(f"File missing during verification: {file_path}")
            mismatches.append(filename)
            continue
        
        try:
            verify_file_integrity(file_path, expected_hash)
        except (DataCorruptionError, FileNotFoundError):
            mismatches.append(filename)
    return mismatches

def download_dataset(url: str, dest_dir: Path, filename: str) -> Path:
    """
    Downloads a dataset file from a URL.
    Implements fail-fast on download failure.
    
    Args:
        url: Source URL.
        dest_dir: Destination directory.
        filename: Name of the file to save as.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        DownloadFailureError: If download fails.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    temp_path = dest_dir / f"{filename}.tmp"

    logger.info(f"Downloading {filename} from {url}...")
    
    try:
        import requests
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            
            with open(temp_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            percent = (downloaded / total) * 100
                            sys.stdout.write(f"\rProgress: {percent:.1f}%")
                            sys.stdout.flush()
            sys.stdout.write("\n")
        
        # Rename temp to final
        shutil.move(str(temp_path), str(dest_path))
        logger.info(f"Download complete: {dest_path}")
        return dest_path

    except Exception as e:
        # Cleanup partial download
        if temp_path.exists():
            temp_path.unlink()
        handle_download_failure(e, url)
        raise

def main() -> None:
    """
    Main entry point for downloading and verifying the EVA-Bench dataset.
    """
    logger.info("Starting EVA-Bench dataset download process.")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    checksum_file = DATA_DIR / "checksums.json"
    
    # Load expected checksums
    expected_checksums = load_existing_checksums(checksum_file)
    if not expected_checksums:
        logger.error("No checksums found. Please ensure data/checksums.json exists.")
        sys.exit(1)

    # Check for existing downloads
    existing_files = list(DATA_DIR.glob("*.wav")) + list(DATA_DIR.glob("*.zip"))
    logger.info(f"Found {len(existing_files)} existing files in {DATA_DIR}")

    # If no files, download
    if len(existing_files) < len(expected_checksums):
        logger.info("Missing files detected. Initiating download.")
        for filename, _ in expected_checksums.items():
            if not (DATA_DIR / filename).exists():
                try:
                    # Assuming URL structure: BASE_URL/filename
                    file_url = f"{DATASET_URL}/{filename}"
                    download_dataset(file_url, DATA_DIR, filename)
                except DownloadFailureError:
                    logger.critical("Download failed. Aborting.")
                    sys.exit(1)
    else:
        logger.info("All files present. Skipping download.")

    # Verify integrity
    logger.info("Verifying downloaded files...")
    mismatches = verify_downloaded_files(DATA_DIR, expected_checksums)
    
    if mismatches:
        logger.critical(f"Corruption detected in {len(mismatches)} files: {mismatches}")
        sys.exit(1)
    
    logger.info("All files verified successfully.")

if __name__ == "__main__":
    main()
