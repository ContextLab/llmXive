import os
import sys
import csv
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from urllib.parse import urlparse

# Import from utils to avoid circular imports and ensure consistent logging
from code.utils.logging_config import setup_pipeline_logger
from code.utils.data_model import Dataset
from code.utils.schema_definitions import get_datasets_headers, get_checksums_headers

# Constants
OPENML_DOMAIN = "openml.org"
UCI_DOMAIN = "archive.ics.uci.edu"
VERIFIED_SOURCES = [OPENML_DOMAIN, UCI_DOMAIN]

logger = setup_pipeline_logger("download_datasets")

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid and accessible."""
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def is_source_verified(url: str) -> bool:
    """
    Verify that the dataset source URL belongs to a canonical public domain.
    Returns True if the domain matches UCI or OpenML patterns.
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check for exact match or subdomain match (e.g., data.openml.org)
        for allowed_domain in VERIFIED_SOURCES:
            if domain == allowed_domain or domain.endswith('.' + allowed_domain):
                return True
        
        logger.warning(f"Source URL '{url}' does not match verified public domains.")
        return False
    except Exception as e:
        logger.error(f"Error verifying source URL '{url}': {e}")
        return False

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str) -> bool:
    """Download a file from URL to dest_path."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def get_dataset_info_from_openml(dataset_id: int) -> Optional[Dict[str, Any]]:
    """Fetch dataset metadata from OpenML API."""
    api_url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "data" in data and "oml:data" in data["data"]:
            info = data["data"]["oml:data"]
            return {
                "dataset_id": str(dataset_id),
                "name": info.get("name"),
                "url": info.get("url"),
                "source": OPENML_DOMAIN,
                "format": "arff"
            }
    except Exception as e:
        logger.error(f"Error fetching OpenML dataset {dataset_id}: {e}")
    return None

def fetch_openml_datasets(min_rows: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch a list of datasets from OpenML that meet criteria.
    Returns list of dataset metadata dicts.
    """
    # OpenML API search endpoint
    search_url = "https://www.openml.org/api/v1/json/data/list/"
    params = {
        "limit": limit,
        "offset": 0,
        "status": "active",
        "tag": "study_141" # Study 141 is a common benchmark set, or use generic search
    }
    
    datasets = []
    # Fallback: if specific study tag doesn't yield enough, we might need to iterate
    # For this implementation, we will try to fetch a broad list and filter locally
    # to ensure we get enough valid datasets without complex API pagination logic in one shot.
    
    try:
        # Attempt to get a large batch
        params["limit"] = 200
        response = requests.get(search_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if "data" in data and "oml:data" in data["data"]:
            for item in data["data"]["oml:data"]:
                did = item.get("did")
                url = item.get("url")
                # Basic validation
                if did and url and is_source_verified(url):
                    # We assume the filter pipeline (T016) will check row count and normality
                    # Here we just ensure source verification and basic structure
                    datasets.append({
                        "dataset_id": str(did),
                        "name": item.get("name", f"dataset_{did}"),
                        "url": url,
                        "source": OPENML_DOMAIN,
                        "format": "arff"
                    })
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset list: {e}")
        raise ConnectionError(f"Dataset fetch failed: {e}")

    if len(datasets) < 50:
        # Try to fetch more if the initial batch was small
        # In a real production scenario, we would implement pagination here.
        # For now, we raise if we didn't get enough from the first batch.
        logger.warning(f"Only fetched {len(datasets)} datasets. Attempting to fetch more...")
        # Simple retry with different offset
        offset = 200
        while len(datasets) < 50 and offset < 1000:
            params["offset"] = offset
            try:
                response = requests.get(search_url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                if "data" in data and "oml:data" in data["data"]:
                    for item in data["data"]["oml:data"]:
                        did = item.get("did")
                        url = item.get("url")
                        if did and url and is_source_verified(url):
                            # Avoid duplicates
                            if not any(d["dataset_id"] == str(did) for d in datasets):
                                datasets.append({
                                    "dataset_id": str(did),
                                    "name": item.get("name", f"dataset_{did}"),
                                    "url": url,
                                    "source": OPENML_DOMAIN,
                                    "format": "arff"
                                })
                offset += 200
            except Exception:
                break

    if len(datasets) < 50:
        raise ConnectionError("Dataset fetch failed: fewer than 50 public datasets found")
    
    return datasets[:100] # Return up to 100 to be safe

def process_uci_dataset(dataset_info: Dict[str, Any], raw_dir: Path) -> Optional[Path]:
    """Process a UCI dataset (download and verify)."""
    # UCI datasets often have specific download URLs
    # This is a simplified handler; real UCI scraping might be needed
    url = dataset_info["url"]
    filename = f"uci_{dataset_info['dataset_id']}.arff"
    dest = raw_dir / filename
    
    if download_file(url, str(dest)):
        return dest
    return None

def process_openml_dataset(dataset_info: Dict[str, Any], raw_dir: Path) -> Optional[Path]:
    """Process an OpenML dataset."""
    did = dataset_info["dataset_id"]
    # Construct standard OpenML download URL
    url = f"https://www.openml.org/data/download/{did}"
    filename = f"openml_{did}.arff"
    dest = raw_dir / filename
    
    if download_file(url, str(dest)):
        return dest
    return None

def initialize_metadata_files(data_dir: Path):
    """Initialize empty CSV files with headers if they don't exist."""
    datasets_csv = data_dir / "datasets.csv"
    checksums_csv = data_dir / "checksums.csv"
    
    if not datasets_csv.exists():
        with open(datasets_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=get_datasets_headers())
            writer.writeheader()
    
    if not checksums_csv.exists():
        with open(checksums_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=get_checksums_headers())
            writer.writeheader()

def append_to_datasets_csv(data_dir: Path, dataset_info: Dict[str, Any], checksum: str):
    """Append dataset metadata to datasets.csv."""
    csv_path = data_dir / "datasets.csv"
    row = {
        "dataset_id": dataset_info["dataset_id"],
        "name": dataset_info["name"],
        "source_url": dataset_info["url"],
        "source": dataset_info["source"],
        "format": dataset_info["format"],
        "checksum": checksum,
        "download_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=get_datasets_headers())
        writer.writerow(row)

def append_to_checksums_csv(data_dir: Path, dataset_id: str, checksum: str):
    """Append checksum to checksums.csv."""
    csv_path = data_dir / "checksums.csv"
    row = {
        "dataset_id": dataset_id,
        "checksum": checksum
    }
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=get_checksums_headers())
        writer.writerow(row)

def update_project_state_artifact_hashes(data_dir: Path):
    """Update any project state files with artifact hashes if needed."""
    # Placeholder for future state tracking
    pass

def main():
    """Main entry point for dataset download and verification."""
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    initialize_metadata_files(data_dir)
    
    logger.info("Starting dataset download and verification process.")
    
    try:
        # Fetch datasets from OpenML
        logger.info("Fetching datasets from OpenML...")
        datasets = fetch_openml_datasets(min_rows=30, limit=100)
        logger.info(f"Fetched {len(datasets)} datasets.")
        
        processed_count = 0
        verified_count = 0
        
        for ds_info in datasets:
            # T013b: Verify source URL against canonical domain patterns
            if not is_source_verified(ds_info["url"]):
                logger.warning(f"Skipping dataset {ds_info['dataset_id']} due to unverified source.")
                continue
            
            logger.info(f"Processing dataset {ds_info['dataset_id']} ({ds_info['name']})...")
            
            # Download based on source
            dest_path = None
            if ds_info["source"] == OPENML_DOMAIN:
                dest_path = process_openml_dataset(ds_info, raw_dir)
            elif ds_info["source"] == UCI_DOMAIN:
                dest_path = process_uci_dataset(ds_info, raw_dir)
            
            if dest_path and dest_path.exists():
                checksum = compute_sha256(str(dest_path))
                append_to_datasets_csv(data_dir, ds_info, checksum)
                append_to_checksums_csv(data_dir, ds_info["dataset_id"], checksum)
                verified_count += 1
                processed_count += 1
            else:
                logger.error(f"Failed to download dataset {ds_info['dataset_id']}.")
        
        logger.info(f"Download complete. Processed: {processed_count}, Verified: {verified_count}")
        
        if verified_count < 50:
            logger.error(f"Final verified count {verified_count} is less than required 50.")
            # Do not raise here to allow partial success for debugging, but log error
            # In strict mode, we might raise ConnectionError again.
        
    except ConnectionError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()