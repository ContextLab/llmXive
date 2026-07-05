"""
Data acquisition module for downloading ABCD Study data.

This module handles downloading, checksum verification, and organization
of raw data files from the ABCD Study portal.
"""

import os
import hashlib
import logging
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional

from code.config import get_project_root, ensure_directories
from code.config_env import get_raw_dir


def calculate_md5(filepath: Path) -> str:
    """
    Calculate the MD5 checksum of a file.

    Args:
        filepath: Path to the file.

    Returns:
        The MD5 checksum as a hexadecimal string.
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def download_file(
    url: str,
    filepath: Path,
    chunk_size: int = 8192
) -> bool:
    """
    Download a file from a URL.

    Args:
        url: The download URL.
        filepath: The destination path.
        chunk_size: Size of chunks to download.

    Returns:
        True if successful, False otherwise.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)

        logging.info(f"Downloaded: {filepath.name}")
        return True

    except requests.RequestException as e:
        logging.error(f"Download failed for {url}: {e}")
        return False


def verify_checksum(filepath: Path, expected_md5: str) -> bool:
    """
    Verify the MD5 checksum of a file.

    Args:
        filepath: Path to the file.
        expected_md5: Expected MD5 checksum.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not filepath.exists():
        return False

    actual_md5 = calculate_md5(filepath)
    match = actual_md5.lower() == expected_md5.lower()

    if not match:
        logging.warning(f"Checksum mismatch for {filepath.name}")
        logging.warning(f"Expected: {expected_md5}, Got: {actual_md5}")

    return match


def acquire_data() -> Dict[str, Path]:
    """
    Acquire ABCD Study data files.

    Returns:
        A dictionary mapping data types to file paths.
    """
    project_root = get_project_root()
    ensure_directories()

    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Define data sources (example URLs - replace with actual ABCD portal URLs)
    # Note: In a real implementation, these would be authenticated endpoints
    data_sources = {
        "phenotypic": {
            "url": "https://example.com/abcd_phenotypic.csv",
            "filename": "abcd_phenotypic.csv",
            "md5": "expected_md5_hash_here"
        },
        "subcortical": {
            "url": "https://example.com/abcd_subcortical.csv",
            "filename": "abcd_subcortical.csv",
            "md5": "expected_md5_hash_here"
        }
    }

    downloaded_files = {}

    for data_type, config in data_sources.items():
        filepath = raw_dir / config["filename"]

        if filepath.exists():
            logging.info(f"File already exists: {filepath.name}")
            if verify_checksum(filepath, config["md5"]):
                downloaded_files[data_type] = filepath
                continue

        logging.info(f"Downloading {data_type} data...")
        if download_file(config["url"], filepath):
            if verify_checksum(filepath, config["md5"]):
                downloaded_files[data_type] = filepath
            else:
                logging.error(f"Checksum verification failed for {data_type}")

    return downloaded_files


def main() -> None:
    """
    Main entry point for the acquisition module.
    """
    logging.basicConfig(level=logging.INFO)
    files = acquire_data()
    for k, v in files.items():
        logging.info(f"{k}: {v}")


if __name__ == "__main__":
    main()
