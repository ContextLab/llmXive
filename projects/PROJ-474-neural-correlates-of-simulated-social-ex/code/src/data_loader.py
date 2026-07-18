"""
Data loader module for fetching fMRI data from OpenNeuro.

This module handles the retrieval of real datasets, specifically
ds000030 (Cyberball task), and validates the presence of required
event markers in the events.tsv files.
"""
import os
import time
import json
import requests
import tarfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from src.config import load_config
from src.utils import get_logger, PipelineError

# Custom exception for data unavailability
class ERR_DATA_UNAVAILABLE(PipelineError):
    """Raised when real data cannot be fetched or validated."""
    pass

# Constants
OPENNEURO_API_URL = "https://openneuro.org/crn/datasets"
DATASET_ID = "ds000030"  # Cyberball task dataset
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

def _get_logger() -> logging.Logger:
    return get_logger(__name__)

def _fetch_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a dataset from OpenNeuro API.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000030')
        
    Returns:
        Dictionary containing dataset metadata
        
    Raises:
        ERR_DATA_UNAVAILABLE: If the dataset cannot be found or fetched
    """
    logger = _get_logger()
    url = f"{OPENNEURO_API_URL}/{dataset_id}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ERR_DATA_UNAVAILABLE(f"Dataset {dataset_id} not found on OpenNeuro")
            else:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: Network error - {e}")
        time.sleep(RETRY_DELAY)
    
    raise ERR_DATA_UNAVAILABLE(f"Failed to fetch dataset {dataset_id} after {MAX_RETRIES} retries")

def _get_download_url(dataset_id: str) -> str:
    """
    Get the direct download URL for the dataset tarball.
    
    Args:
        dataset_id: The OpenNeuro dataset ID
        
    Returns:
        URL to download the dataset
        
    Raises:
        ERR_DATA_UNAVAILABLE: If download URL cannot be determined
    """
    logger = _get_logger()
    # OpenNeuro dataset download URL pattern
    # Note: This might need adjustment based on OpenNeuro API changes
    base_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/download"
    
    # For ds000030, we use the standard download link
    # OpenNeuro typically provides a direct link for the latest version
    return f"https://openneuro.org/datasets/{dataset_id}/download"

def _download_and_extract_dataset(dataset_id: str, output_dir: Path) -> Path:
    """
    Download the dataset from OpenNeuro and extract it.
    
    Args:
        dataset_id: The OpenNeuro dataset ID
        output_dir: Directory where the dataset will be extracted
        
    Returns:
        Path to the extracted dataset directory
        
    Raises:
        ERR_DATA_UNAVAILABLE: If download or extraction fails
    """
    logger = _get_logger()
    download_url = f"https://openneuro.org/datasets/{dataset_id}/download"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_tar_path = output_dir / f"{dataset_id}.tar.gz"
    
    logger.info(f"Downloading dataset {dataset_id} from {download_url}...")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(download_url, stream=True, timeout=300)
            if response.status_code == 200:
                with open(temp_tar_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info("Download completed. Extracting...")
                break
            else:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: HTTP {response.status_code}")
                if attempt == MAX_RETRIES - 1:
                    raise ERR_DATA_UNAVAILABLE(f"Failed to download dataset: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES}: Network error - {e}")
            if attempt == MAX_RETRIES - 1:
                raise ERR_DATA_UNAVAILABLE(f"Failed to download dataset: {e}")
        time.sleep(RETRY_DELAY)
    
    # Extract the tarball
    try:
        with tarfile.open(temp_tar_path, 'r:gz') as tar:
            tar.extractall(path=output_dir)
        
        # Clean up tarball
        temp_tar_path.unlink()
        
        # Find the extracted directory (usually named after the dataset)
        extracted_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith(dataset_id)]
        if not extracted_dirs:
            raise ERR_DATA_UNAVAILABLE(f"Could not find extracted dataset directory")
        
        extracted_path = extracted_dirs[0]
        logger.info(f"Dataset extracted to: {extracted_path}")
        return extracted_path
        
    except tarfile.TarError as e:
        raise ERR_DATA_UNAVAILABLE(f"Failed to extract dataset: {e}")

def _validate_events_tsv(dataset_path: Path) -> None:
    """
    Validate that events.tsv files contain required Inclusion/Exclusion markers.
    
    Args:
        dataset_path: Path to the extracted dataset directory
        
    Raises:
        ERR_DATA_UNAVAILABLE: If required markers are missing
    """
    logger = _get_logger()
    events_files = list(dataset_path.rglob("events.tsv"))
    
    if not events_files:
        raise ERR_DATA_UNAVAILABLE("No events.tsv files found in dataset")
    
    required_markers = ["Inclusion", "Exclusion"]
    found_markers = set()
    
    for events_file in events_files:
        logger.info(f"Validating events file: {events_file}")
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                for marker in required_markers:
                    if marker.lower() in content:
                        found_markers.add(marker)
        except Exception as e:
            logger.warning(f"Could not read {events_file}: {e}")
            continue
    
    missing_markers = set(required_markers) - found_markers
    if missing_markers:
        raise ERR_DATA_UNAVAILABLE(
            f"Missing required event markers in events.tsv: {missing_markers}. "
            f"Required: {required_markers}"
        )
    
    logger.info(f"Validated events.tsv files. Found markers: {found_markers}")

def load_openneuro_dataset(
    dataset_id: str = DATASET_ID,
    base_data_dir: Optional[Path] = None
) -> Path:
    """
    Main function to load an OpenNeuro dataset.
    
    This function:
    1. Fetches dataset metadata
    2. Downloads and extracts the dataset
    3. Validates the presence of required event markers
    
    Args:
        dataset_id: The OpenNeuro dataset ID (default: 'ds000030')
        base_data_dir: Base directory for data storage (default: from config)
        
    Returns:
        Path to the extracted dataset directory
        
    Raises:
        ERR_DATA_UNAVAILABLE: If fetch, download, or validation fails
    """
    logger = _get_logger()
    
    # Load configuration to get data paths
    config = load_config()
    if base_data_dir is None:
        base_data_dir = Path(config.get("paths", {}).get("raw_data", "data/raw"))
    
    base_data_dir = Path(base_data_dir)
    base_data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading OpenNeuro dataset: {dataset_id}")
    
    # Step 1: Fetch metadata (to verify dataset exists)
    try:
        metadata = _fetch_dataset_metadata(dataset_id)
        logger.info(f"Dataset metadata fetched: {metadata.get('id', 'unknown')}")
    except ERR_DATA_UNAVAILABLE:
        raise
    
    # Step 2: Download and extract
    try:
        dataset_path = _download_and_extract_dataset(dataset_id, base_data_dir)
    except ERR_DATA_UNAVAILABLE:
        raise
    
    # Step 3: Validate events.tsv
    try:
        _validate_events_tsv(dataset_path)
    except ERR_DATA_UNAVAILABLE:
        raise
    
    logger.info(f"Dataset {dataset_id} successfully loaded and validated at {dataset_path}")
    return dataset_path

def main():
    """
    Main entry point for the data loader script.
    
    Downloads the dataset and prints the path to the extracted directory.
    """
    logger = _get_logger()
    logger.info("Starting OpenNeuro dataset loader")
    
    try:
        dataset_path = load_openneuro_dataset()
        print(f"Dataset loaded successfully: {dataset_path}")
        
        # Save a metadata file about the loaded dataset
        metadata_path = dataset_path.parent / "loaded_dataset_info.json"
        metadata = {
            "dataset_id": DATASET_ID,
            "load_path": str(dataset_path),
            "status": "success"
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_path}")
        
    except ERR_DATA_UNAVAILABLE as e:
        logger.error(f"Data unavailable: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
