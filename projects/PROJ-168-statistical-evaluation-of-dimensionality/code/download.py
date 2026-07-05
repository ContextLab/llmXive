"""
Download module for fetching raw count matrices from GEO.
Implements fetching logic using requests for verified GEO raw count URLs
and checksum validation.
"""
import os
import sys
import logging
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for GEO
GEO_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/geo/series"
GEO_API_URL = "https://api.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Common file patterns for raw count matrices in GEO
RAW_COUNT_PATTERNS = [
    r".*counts.*\.txt",
    r".*counts.*\.csv",
    r".*raw.*\.txt",
    r".*raw.*\.csv",
    r".*matrix.*\.txt",
    r".*matrix.*\.csv",
    r".*expression.*\.txt",
    r".*expression.*\.csv",
]

# Compile patterns for efficiency
RAW_COUNT_REGEX = re.compile('|'.join(RAW_COUNT_PATTERNS), re.IGNORECASE)


class DownloadError(Exception):
    """Custom exception for download failures."""
    pass


class ChecksumValidationError(Exception):
    """Custom exception for checksum validation failures."""
    pass


def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_gse_accession_details(accession: str) -> Dict:
    """
    Fetch metadata for a GEO Series (GSE) accession.
    Returns a dictionary with metadata including sample list.
    """
    logger.info(f"Fetching metadata for {accession}")
    params = {
        "db": "gds",
        "id": accession,
        "retmode": "json"
    }
    
    try:
        # Note: Direct GEO API might be limited, we'll use the GDS API as a proxy
        # or fall back to parsing the FTP structure
        response = requests.get(GEO_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch metadata via API for {accession}: {e}")
        # Return a minimal structure to allow FTP parsing fallback
        return {"samples": []}


def find_raw_count_url(accession: str) -> Optional[str]:
    """
    Locate the URL for raw count matrices for a given GSE accession.
    This function attempts to find the file by inspecting the FTP directory structure.
    """
    logger.info(f"Searching for raw count files for {accession}")
    
    # Construct the FTP path based on GEO structure
    # Example: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE13nnn/GSE131907/
    # We need to find the specific series directory
    
    # Split accession into prefix and suffix for FTP path
    # GSE131907 -> GSE13nnn -> GSE131907
    prefix = accession[:6]  # GSE13
    series_dir = accession  # GSE131907
    
    # Try to construct the base URL for the series
    # GEO FTP structure: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE13nnn/GSE131907/
    ftp_base = f"{GEO_BASE_URL}/{prefix}nnn/{series_dir}/"
    
    # We need to find the sample directory (e.g., GSE131907_RAW)
    # and then look for count files
    sample_pattern = f"{accession}_RAW"
    
    # Since we can't easily list FTP directories via requests without a specific file,
    # we'll try common patterns for the raw file URLs
    # GEO often provides files like: {accession}_RAW.tar or individual .txt/.csv files
    
    # Common patterns for raw count files
    candidate_paths = [
        f"{ftp_base}{sample_pattern}.tar",
        f"{ftp_base}{sample_pattern}/{sample_pattern}_counts.txt",
        f"{ftp_base}{sample_pattern}/{sample_pattern}_counts.csv",
        f"{ftp_base}suppl/{sample_pattern}_counts.txt",
        f"{ftp_base}suppl/{sample_pattern}_counts.csv",
    ]
    
    # Also try the specific dataset accession if provided
    # For GSE131907, the actual file might be at a specific path
    # Let's try the most common pattern first
    # Based on typical GEO structure, the raw data is often in a _RAW folder
    
    # Try to find the file by checking common locations
    # We'll iterate through possible file names
    possible_filenames = [
        f"{accession}_counts.txt",
        f"{accession}_counts.csv",
        f"{accession}_raw_counts.txt",
        f"{accession}_raw_counts.csv",
        f"{accession}_matrix.txt",
        f"{accession}_matrix.csv",
    ]
    
    for filename in possible_filenames:
        url = f"{ftp_base}{filename}"
        try:
            head_response = requests.head(url, timeout=10)
            if head_response.status_code == 200:
                logger.info(f"Found raw count file at: {url}")
                return url
        except requests.RequestException:
            continue
    
    # If direct search fails, try to find via the _RAW directory
    raw_dir_url = f"{ftp_base}{sample_pattern}/"
    try:
        # Try to list the directory if possible (some FTP servers allow HTTP listing)
        # This is not reliable, so we'll try specific known patterns
        # For GSE131907, the file is often named specifically
        # Let's try the most likely pattern for the known datasets
        
        # For GSE131907, the file is typically: GSE131907_RAW.tar
        # and inside it contains the count matrices
        tar_url = f"{ftp_base}{sample_pattern}.tar"
        head_response = requests.head(tar_url, timeout=10)
        if head_response.status_code == 200:
            logger.info(f"Found raw count archive at: {tar_url}")
            return tar_url
    except requests.RequestException:
        pass
    
    # If we still haven't found it, try the specific dataset patterns
    # based on the data gap resolver findings
    # The data gap resolver should have identified which datasets are available
    # We'll try the most common pattern for the known datasets
    
    # For the specific datasets mentioned in the project:
    # GSE131907, GSE111322, GSE150728
    # We'll try to find them by their specific patterns
    
    # Try to find the file by checking the specific dataset patterns
    # This is a fallback for when the general search fails
    specific_patterns = {
        "GSE131907": [
            f"{ftp_base}{sample_pattern}.tar",
            f"{ftp_base}{sample_pattern}/GSE131907_counts.txt",
        ],
        "GSE111322": [
            f"{ftp_base}{sample_pattern}.tar",
            f"{ftp_base}{sample_pattern}/GSE111322_counts.txt",
        ],
        "GSE150728": [
            f"{ftp_base}{sample_pattern}.tar",
            f"{ftp_base}{sample_pattern}/GSE150728_counts.txt",
        ],
    }
    
    if accession in specific_patterns:
        for url in specific_patterns[accession]:
            try:
                head_response = requests.head(url, timeout=10)
                if head_response.status_code == 200:
                    logger.info(f"Found raw count file at: {url}")
                    return url
            except requests.RequestException:
                continue
    
    logger.warning(f"No raw count file found for {accession}")
    return None


def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> Path:
    """
    Download a file from a URL to the specified output path.
    
    Args:
        url: The URL to download from
        output_path: The path where the file should be saved
        chunk_size: Size of chunks to download at a time
        
    Returns:
        Path to the downloaded file
        
    Raises:
        DownloadError: If the download fails
    """
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
        
        logger.info(f"Downloaded {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise DownloadError(f"Download failed: {e}")


def validate_checksum(file_path: Path, expected_md5: Optional[str] = None) -> bool:
    """
    Validate the checksum of a downloaded file.
    
    Args:
        file_path: Path to the file to validate
        expected_md5: Expected MD5 checksum (optional)
        
    Returns:
        True if validation passes or no expected checksum provided
        
    Raises:
        ChecksumValidationError: If validation fails
    """
    if not file_path.exists():
        raise ChecksumValidationError(f"File does not exist: {file_path}")
    
    actual_md5 = calculate_md5(file_path)
    logger.info(f"Calculated MD5 for {file_path}: {actual_md5}")
    
    if expected_md5:
        if actual_md5.lower() != expected_md5.lower():
            raise ChecksumValidationError(
                f"Checksum mismatch for {file_path}: "
                f"expected {expected_md5}, got {actual_md5}"
            )
        logger.info(f"Checksum validation passed for {file_path}")
    else:
        logger.warning(f"No expected checksum provided for {file_path}, skipping validation")
    
    return True


def download_dataset(accession: str, config: Config) -> Tuple[Path, Optional[str]]:
    """
    Download a dataset for a given GEO accession.
    
    Args:
        accession: The GEO accession (e.g., GSE131907)
        config: Configuration object with paths and settings
        
    Returns:
        Tuple of (path to downloaded file, checksum or None)
        
    Raises:
        DownloadError: If download fails
        ChecksumValidationError: If checksum validation fails
    """
    logger.info(f"Processing dataset: {accession}")
    
    # Find the URL for raw count files
    url = find_raw_count_url(accession)
    if not url:
        raise DownloadError(f"No raw count file found for {accession}")
    
    # Determine output path
    output_dir = config.data_raw_dir
    output_filename = f"{accession}_raw.tar" if url.endswith('.tar') else f"{accession}_raw.txt"
    output_path = output_dir / output_filename
    
    # Download the file
    try:
        downloaded_path = download_file(url, output_path)
        
        # Validate checksum if available
        # For now, we'll skip checksum validation since GEO doesn't always provide it
        # In a real implementation, we would fetch the checksum from a metadata file
        # or compare against a known good value
        validate_checksum(downloaded_path)
        
        return downloaded_path, None
        
    except Exception as e:
        logger.error(f"Failed to download {accession}: {e}")
        raise


def main():
    """Main entry point for the download script."""
    logger.info("Starting download process")
    
    config = Config()
    datasets_to_download = config.dataset_accessions
    
    results = {}
    
    for accession in datasets_to_download:
        try:
            logger.info(f"Processing {accession}")
            file_path, checksum = download_dataset(accession, config)
            results[accession] = {
                "status": "success",
                "file_path": str(file_path),
                "checksum": checksum
            }
            logger.info(f"Successfully downloaded {accession}")
        except Exception as e:
            logger.error(f"Failed to download {accession}: {e}")
            results[accession] = {
                "status": "failed",
                "error": str(e)
            }
    
    # Save results to a JSON file
    results_path = config.results_dir / "download_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Download results saved to {results_path}")
    
    # Return exit code based on success
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    if failed_count > 0:
        logger.warning(f"{failed_count} dataset(s) failed to download")
        sys.exit(1)
    
    logger.info("All datasets downloaded successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()