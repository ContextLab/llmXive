"""
Module for downloading VAERS datasets.

This module handles fetching CSV files from the VAERS website or verified mirrors,
saving them to the local data/raw directory, and verifying file integrity using checksums.
"""
import os
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for VAERS data (example, may need update based on actual source)
VAERS_BASE_URL = "https://vaers.hhs.gov/data/datasets"
# Or a mirror if the official site is unstable
# VAERS_BASE_URL = "https://mirror.example.com/vaers"

# Define years to download
DOWNLOAD_YEARS = [2020, 2021, 2022, 2023]

def calculate_checksum(data: bytes, algorithm: str = "md5") -> str:
    """
    Calculate the checksum of the given data.

    Args:
        data: The binary data to hash.
        algorithm: The hashing algorithm to use (default: 'md5').

    Returns:
        The hexadecimal checksum string.

    Raises:
        ValueError: If an unsupported algorithm is provided.
    """
    if algorithm.lower() == "md5":
        hasher = hashlib.md5()
    elif algorithm.lower() == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    hasher.update(data)
    return hasher.hexdigest()

def verify_checksum(data: bytes, expected_hash: str, algorithm: str = "md5") -> bool:
    """
    Verify if the checksum of the data matches the expected hash.

    Args:
        data: The binary data to check.
        expected_hash: The expected hexadecimal checksum.
        algorithm: The hashing algorithm used.

    Returns:
        True if the checksums match, False otherwise.
    """
    calculated_hash = calculate_checksum(data, algorithm)
    # Compare case-insensitively
    return calculated_hash.lower() == expected_hash.lower()

def download_file(url: str, output_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Download a file from a URL and optionally verify its checksum.

    Args:
        url: The URL to download from.
        output_path: The local path to save the file.
        expected_checksum: Optional expected checksum to verify against.

    Returns:
        True if download and verification (if applicable) succeed, False otherwise.
    """
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download content
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
        
        # Write to disk
        with open(output_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Downloaded {len(content)} bytes to {output_path}")
        
        # Verify checksum if provided
        if expected_checksum:
            logger.info(f"Verifying checksum for {output_path}")
            if not verify_checksum(content, expected_checksum):
                logger.error(f"Checksum mismatch for {output_path}")
                # Optionally remove the file if checksum fails
                os.remove(output_path)
                return False
            logger.info(f"Checksum verified for {output_path}")
        
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except IOError as e:
        logger.error(f"Failed to write file {output_path}: {e}")
        return False

def get_checksum_url(base_url: str, filename: str) -> str:
    """
    Construct the URL for the checksum file (e.g., .md5).
    Assumes the checksum file is in the same directory with a .md5 extension.
    """
    # VAERS often provides .md5 files alongside the data
    return f"{base_url}/{filename}.md5"

def download_vaers_data(years: list = DOWNLOAD_YEARS, base_url: str = VAERS_BASE_URL, output_dir: str = "data/raw") -> Dict[str, Any]:
    """
    Download VAERS data for specified years.

    Args:
        years: List of years to download.
        base_url: Base URL for VAERS data.
        output_dir: Directory to save downloaded files.

    Returns:
        A dictionary with download status and file paths.
    """
    results = {"success": [], "failed": [], "files": {}}
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for year in years:
        # Construct filename - VAERS naming convention varies, this is an example
        # Typically: vaersdata{year}.csv
        filename = f"vaersdata{year}.csv"
        url = f"{base_url}/{filename}"
        checksum_url = get_checksum_url(base_url, filename)
        
        local_path = str(output_path / filename)
        
        # Try to fetch checksum first if it exists
        expected_checksum = None
        try:
            # Check if checksum file exists (simplified check, might need HEAD request)
            # For robustness, we assume the checksum file exists if the data file does
            # In a real scenario, we might try to fetch it and handle 404
            checksum_resp = requests.get(checksum_url, timeout=10)
            if checksum_resp.status_code == 200:
                # The checksum file usually contains just the hash and filename
                # We extract the hash
                checksum_content = checksum_resp.text.strip()
                # Assuming format: "hash  filename" or just "hash"
                expected_checksum = checksum_content.split()[0]
                logger.info(f"Found checksum for {filename}: {expected_checksum}")
            else:
                logger.warning(f"Checksum file not found for {filename}, skipping verification")
        except requests.exceptions.RequestException:
            logger.warning(f"Could not fetch checksum for {filename}, skipping verification")
        
        success = download_file(url, local_path, expected_checksum)
        
        if success:
            results["success"].append(year)
            results["files"][year] = local_path
        else:
            results["failed"].append(year)
    
    return results

def main():
    """Main entry point for the download script."""
    logger.info("Starting VAERS data download")
    results = download_vaers_data()
    
    if results["failed"]:
        logger.error(f"Failed to download data for years: {results['failed']}")
        exit(1)
    else:
        logger.info(f"Successfully downloaded data for years: {results['success']}")
        for year, path in results["files"].items():
            logger.info(f"  {year}: {path}")
        exit(0)

if __name__ == "__main__":
    main()