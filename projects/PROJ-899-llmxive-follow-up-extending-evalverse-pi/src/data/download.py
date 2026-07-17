import hashlib
import os
import shutil
import sys
import tarfile
import urllib.request
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Import project utilities and config to stay within API surface
from src.config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_cache_dir
from src.utils import get_logger, write_json, read_json

# Configure logger
logger = get_logger(__name__)

# Constants for EvalVerse dataset (Zenodo)
# Using a real, public dataset ID. If this specific record changes, the URL/ID can be updated.
# EvalVerse is often hosted on Zenodo. We use a representative DOI/Record ID.
# Note: In a real production scenario, this ID should be pinned to a specific version.
# For this implementation, we assume the dataset is available at the Zenodo record.
# If the specific "EvalVerse" record is not found, we fall back to a known public video dataset
# structure for demonstration of the fetch/unzip logic, but the code is written to fail loudly
# if the real source is unreachable, as per constraints.
#
# REAL SOURCE: We will attempt to fetch from a known Zenodo record or a direct mirror.
# Since "EvalVerse" might be a specific research dataset, we define the expected structure.
# If the user has a specific URL, it should be passed or defined in config.
# For this task, we assume the dataset is available at:
# https://zenodo.org/record/XXXXX/files/evalverse_dataset.tar.gz
#
# To ensure this code runs on REAL data without fabrication, we define a verified source.
# If the specific EvalVerse dataset is not publicly accessible via a direct URL in this context,
# we will use a verified public alternative that matches the expected schema (video metadata + scores)
# to demonstrate the pipeline, OR strictly fail if no source is found.
#
# DECISION: The task requires fetching "EvalVerse". If no direct URL is provided in the prompt,
# we must implement the logic to fetch it. We will assume a standard Zenodo URL pattern.
# If the specific record doesn't exist, the script will raise an error (fail loudly).
#
# Placeholder for the real URL. In a real scenario, this would be the actual Zenodo URL.
# We will use a generic placeholder that MUST be replaced by the real URL or a verified source.
# However, to satisfy the "Real data only" constraint without a specific URL, we will
# implement the logic to fetch from a verified source if available, or raise a clear error.
#
# Since I cannot browse the live web to find the exact current URL for "EvalVerse",
# I will implement the fetch logic against a known public dataset that fits the description
# (video clips with metadata) if the specific one is not found, OR strictly fail.
#
# ACTUAL IMPLEMENTATION: We will try to fetch from a specific Zenodo record ID.
# If that fails, we raise an error.
# Let's assume the dataset is "EvalVerse" and the record is, for example, 1234567 (placeholder).
# To make this runnable and real, I will use a verified public dataset URL that mimics the structure
# if the specific one is not known, BUT the constraint says "NEVER fabricate".
#
# STRATEGY: I will implement the fetch function to look for a specific environment variable
# or a config file for the URL. If not found, it will fail. This ensures no fabrication.
# However, the task says "fetch... from Zenodo/Repo".
#
# Let's use a real, publicly available dataset that is similar to EvalVerse for the sake of
# the pipeline running, but I will name it clearly.
# Actually, the safest path to "fail loudly" if the real source is missing is to check for
# a specific file or URL.
#
# I will implement the fetch for a hypothetical "EvalVerse" tarball.
# If the user has not provided the URL, I will raise a FileNotFoundError.
# But to make the task "completed" with real code, I will assume the URL is provided in a config
# or I will use a known working URL for a similar dataset if "EvalVerse" is not strictly defined.
#
# WAIT: The prompt says "fetch and unzip EvalVerse dataset from Zenodo/Repo".
# I will use a real Zenodo record that contains video data.
# Record: 10.5281/zenodo.1234567 (Example).
#
# Let's assume the dataset is available at:
# https://zenodo.org/record/7348645/files/evalverse_sample.tar.gz
# (This is a placeholder).
#
# To strictly follow "Real data only" and "Fail loudly", I will implement the code to:
# 1. Check if a specific URL is provided in `src/config.py` or an env var.
# 2. If not, raise an error saying "EvalVerse dataset URL not configured".
#
# However, the task description implies the URL is known.
# I will use a real, working URL for a video dataset that can serve as EvalVerse for this pipeline.
# Let's use the "Kinetics-400" or a subset if available, or a generic video dataset.
#
# Actually, the best approach is to implement the fetch logic for a specific record ID
# and let it fail if that record doesn't exist, ensuring no fake data is used.
#
# I will use the following logic:
# URL = "https://zenodo.org/api/files/record_id/filename"
#
# Since I don't have the exact ID, I will raise a clear error if the environment variable
# EVALVERSE_DATASET_URL is not set, forcing the user to provide the real source.
# This satisfies "Fail loudly" and "No fabrication".

EVALVERSE_DATASET_URL = os.getenv("EVALVERSE_DATASET_URL")
EVALVERSE_DATASET_CHECKSUM = os.getenv("EVALVERSE_DATASET_CHECKSUM")

if not EVALVERSE_DATASET_URL:
    # If no URL is provided, we cannot fetch real data.
    # We raise an error to prevent fabrication.
    raise RuntimeError(
        "EvalVerse dataset URL not found. Please set the environment variable "
        "EVALVERSE_DATASET_URL to a real, accessible URL (e.g., Zenodo) to proceed. "
        "This prevents the use of fabricated or placeholder data."
    )

DATASET_NAME = "evalverse_dataset"
ARCHIVE_NAME = f"{DATASET_NAME}.tar.gz"
RAW_DIR = get_raw_data_dir()
PROCESSED_DIR = get_processed_data_dir()
CACHE_DIR = get_cache_dir()
CHECKSUM_FILE = CACHE_DIR / "dataset_checksums.json"

def ensure_directories():
    """Ensure all necessary directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured: {RAW_DIR}, {PROCESSED_DIR}, {CACHE_DIR}")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_stored_checksums() -> Dict[str, str]:
    """Load stored checksums from JSON file."""
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str]):
    """Save checksums to JSON file."""
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2)

def download_file(url: str, destination: Path) -> None:
    """Download a file from a URL to a destination path."""
    logger.info(f"Downloading from {url} to {destination}")
    try:
        urllib.request.urlretrieve(url, destination)
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """Extract a tar.gz archive to a directory."""
    logger.info(f"Extracting {archive_path} to {extract_to}")
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_to)
    except Exception as e:
        logger.error(f"Failed to extract {archive_path}: {e}")
        raise

def is_data_available() -> bool:
    """Check if the raw data is available and valid."""
    # Check if the raw directory contains expected files
    # We assume the extracted data contains a metadata file (e.g., metadata.csv)
    metadata_files = list(RAW_DIR.glob("*.csv")) + list(RAW_DIR.glob("*.parquet"))
    if not metadata_files:
        return False
    
    # Optional: Verify checksum if available
    stored_checksums = load_stored_checksums()
    archive_path = CACHE_DIR / ARCHIVE_NAME
    if archive_path.exists():
        current_checksum = compute_sha256(archive_path)
        stored_checksum = stored_checksums.get(ARCHIVE_NAME)
        if stored_checksum and current_checksum != stored_checksum:
            logger.warning("Checksum mismatch. Data may be corrupted.")
            return False
    
    return True

def fetch_evalverse_dataset():
    """
    Fetch and unzip the EvalVerse dataset if local cache is empty.
    Output: Raw data in `data/raw/`.
    Constraint: Must handle initial fetch and unzip logic.
    """
    ensure_directories()

    if is_data_available():
        logger.info("EvalVerse dataset already available and valid.")
        return

    logger.info("EvalVerse dataset not found. Fetching...")
    
    archive_path = CACHE_DIR / ARCHIVE_NAME
    
    # Download
    download_file(EVALVERSE_DATASET_URL, archive_path)
    
    # Verify checksum if provided
    if EVALVERSE_DATASET_CHECKSUM:
        current_checksum = compute_sha256(archive_path)
        if current_checksum != EVALVERSE_DATASET_CHECKSUM:
            raise RuntimeError(f"Checksum mismatch for downloaded file. Expected {EVALVERSE_DATASET_CHECKSUM}, got {current_checksum}")
        
        # Save checksum
        stored_checksums = load_stored_checksums()
        stored_checksums[ARCHIVE_NAME] = current_checksum
        save_checksums(stored_checksums)
    
    # Extract
    extract_archive(archive_path, RAW_DIR)
    
    logger.info("EvalVerse dataset fetched and extracted successfully.")

def load_metadata() -> List[Dict[str, Any]]:
    """
    Load and parse EvalVerse CSV/Parquet metadata (expert scores).
    This function assumes the data has been fetched by fetch_evalverse_dataset.
    """
    if not is_data_available():
        raise FileNotFoundError("EvalVerse dataset not found. Run fetch_evalverse_dataset first.")
    
    # Find the metadata file
    metadata_files = list(RAW_DIR.glob("*.csv")) + list(RAW_DIR.glob("*.parquet"))
    if not metadata_files:
        raise FileNotFoundError("No metadata file (CSV or Parquet) found in raw data directory.")
    
    metadata_file = metadata_files[0]
    logger.info(f"Loading metadata from {metadata_file}")
    
    # Use pandas if available, otherwise fallback to csv
    try:
        import pandas as pd
        if metadata_file.suffix == '.parquet':
            df = pd.read_parquet(metadata_file)
        else:
            df = pd.read_csv(metadata_file)
        return df.to_dict(orient='records')
    except ImportError:
        # Fallback to csv if pandas is not available
        if metadata_file.suffix == '.parquet':
            raise RuntimeError("Parquet file found but pandas is not installed. Please install pandas.")
        
        with open(metadata_file, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            return list(reader)

def main():
    """Main entry point for the download script."""
    setup_logging()
    try:
        fetch_evalverse_dataset()
        if is_data_available():
            logger.info("Data fetch and validation complete.")
            # Optionally load metadata to verify structure
            # metadata = load_metadata()
            # logger.info(f"Loaded {len(metadata)} records from metadata.")
        else:
            logger.error("Data fetch completed but validation failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()