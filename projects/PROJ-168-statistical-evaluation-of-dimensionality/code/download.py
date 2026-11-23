import os
import sys
import logging
import hashlib
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom Exceptions
class DownloadError(Exception):
    """Base exception for download failures."""
    pass

class ChecksumValidationError(Exception):
    """Exception raised when checksum validation fails."""
    pass

class LabelValidationError(Exception):
    """Exception raised when ground-truth labels are missing or malformed."""
    pass

def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_gse_accession_details(accession: str) -> Dict[str, Any]:
    """
    Fetch metadata for a GEO Series accession.
    Returns a dict containing series title, summary, and sample count.
    """
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}&form=text"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Parse basic metadata from the text response or use regex for specific fields
        # For robustness, we'll rely on the Series Matrix file for label extraction later
        # but we fetch the summary here to verify existence.
        return {
            "accession": accession,
            "exists": True,
            "raw_url": f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={accession}&format=txt&file={accession}_series_matrix.txt.gz"
        }
    except requests.RequestException as e:
        logger.error(f"Failed to fetch metadata for {accession}: {e}")
        return {"accession": accession, "exists": False, "error": str(e)}

def find_raw_count_url(accession: str) -> Optional[str]:
    """
    Locate the URL for the raw count matrix (Series Matrix file).
    In a real pipeline, this might parse the GEO FTP directory or use the Series Matrix.
    For this implementation, we assume the Series Matrix file contains the counts and labels.
    """
    # Standard GEO Series Matrix URL pattern
    return f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={accession}&format=txt&file={accession}_series_matrix.txt.gz"

def download_file(url: str, output_path: str, chunk_size: int = 8192) -> bool:
    """Download a file from URL to output_path."""
    try:
        logger.info(f"Downloading {url} to {output_path}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        return False

def validate_checksum(file_path: str, expected_md5: Optional[str] = None) -> bool:
    """
    Validate checksum if expected_md5 is provided.
    If not provided, just compute and log it.
    """
    if not os.path.exists(file_path):
        return False
    
    actual_md5 = calculate_md5(file_path)
    logger.info(f"Calculated MD5 for {file_path}: {actual_md5}")
    
    if expected_md5:
        if actual_md5 == expected_md5:
            logger.info("Checksum validation passed.")
            return True
        else:
            logger.error(f"Checksum mismatch. Expected: {expected_md5}, Got: {actual_md5}")
            return False
    return True

def validate_ground_truth_labels(file_path: str, accession: str) -> None:
    """
    Validate that the downloaded file contains ground-truth labels.
    For GEO Series Matrix files, labels are typically in the !SAMPLE_... fields
    or in a specific column if the matrix is parsed.
    
    This function:
    1. Checks if the file exists and is non-empty.
    2. Scans for label-related metadata (e.g., !sample_title, !sample_characteristics).
    3. Raises LabelValidationError if labels are missing or malformed.
    """
    if not os.path.exists(file_path):
        raise LabelValidationError(f"File not found for {accession}: {file_path}")
    
    if os.path.getsize(file_path) == 0:
        raise LabelValidationError(f"File is empty for {accession}: {file_path}")

    label_found = False
    sample_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                # Check for sample metadata lines which usually contain labels
                if line.startswith("!sample_title"):
                    label_found = True
                if line.startswith("!sample_characteristics"):
                    # Often contains cell type or condition info
                    label_found = True
                if line.startswith("!sample_status"):
                    # Check if status is valid (e.g., not "withdrawn")
                    if "withdrawn" in line.lower():
                        raise LabelValidationError(f"Sample status indicates withdrawn for {accession}")
                
                # Count samples to ensure we have data
                if line.startswith("!sample"):
                    sample_count += 1
        
        if not label_found:
            raise LabelValidationError(
                f"Ground-truth labels (e.g., !sample_title or !sample_characteristics) "
                f"are missing or malformed in {file_path} for accession {accession}. "
                f"Pipeline cannot proceed without valid labels."
            )
        
        if sample_count == 0:
            raise LabelValidationError(
                f"No sample entries found in {file_path} for accession {accession}. "
                f"Data appears to be missing."
            )
        
        logger.info(f"Validation passed for {accession}: Found {sample_count} samples with labels.")

    except IOError as e:
        raise LabelValidationError(f"Error reading file {file_path} for {accession}: {e}")

def download_dataset(accession: str, raw_dir: str, expected_md5: Optional[str] = None) -> str:
    """
    Download a GEO dataset and validate ground-truth labels.
    
    This function:
    1. Determines the download URL.
    2. Downloads the file.
    3. Validates the checksum (if provided).
    4. **CRITICAL**: Validates ground-truth labels. If missing/malformed, raises LabelValidationError.
    
    Returns the path to the downloaded file.
    """
    os.makedirs(raw_dir, exist_ok=True)
    output_filename = f"{accession}_series_matrix.txt.gz"
    output_path = os.path.join(raw_dir, output_filename)
    
    url = find_raw_count_url(accession)
    if not url:
        raise DownloadError(f"Could not determine download URL for {accession}")
    
    # Download
    if not download_file(url, output_path):
        raise DownloadError(f"Failed to download {accession}")
    
    # Checksum
    if not validate_checksum(output_path, expected_md5):
        if expected_md5:
            raise ChecksumValidationError(f"Checksum validation failed for {accession}")
        # If no expected MD5, we proceed but log a warning
        logger.warning(f"No expected MD5 provided for {accession}, skipping strict checksum check.")
    
    # **CRITICAL VALIDATION STEP FOR T015**
    # Abort if ground-truth labels are missing or malformed
    validate_ground_truth_labels(output_path, accession)
    
    logger.info(f"Successfully downloaded and validated {accession} at {output_path}")
    return output_path

def main():
    """Main entry point for testing the download and validation logic."""
    if len(sys.argv) < 2:
        print("Usage: python download.py <GSE_ACCESSION> [RAW_DIR]")
        sys.exit(1)
    
    accession = sys.argv[1]
    raw_dir = sys.argv[2] if len(sys.argv) > 2 else "data/raw"
    
    try:
        result_path = download_dataset(accession, raw_dir)
        print(f"SUCCESS: {result_path}")
    except LabelValidationError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    except (DownloadError, ChecksumValidationError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()