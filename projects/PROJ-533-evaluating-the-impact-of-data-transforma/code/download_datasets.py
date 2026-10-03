import os
import sys
import csv
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
import json

# Import from local utils as per API surface
from code.utils.logging_config import setup_pipeline_logger
from code.utils.checkpointing import save_state, load_state

# Constants
CANONICAL_DOMAINS = [
    "openml.org",
    "archive.ics.uci.edu",
    "archive.ics.uci.edu", # Duplicate check handled by logic
    "www.openml.org",
    "www.ics.uci.edu"
]
REQUIRED_HEADERS = [
    "dataset_id", "source_url", "num_rows", "num_cols", 
    "target_variable", "checksum", "source_verified", "fetch_time"
]
CHECKSUMS_HEADERS = ["dataset_id", "checksum", "file_path"]

# Logger setup
logger = setup_pipeline_logger("download_datasets")

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    if not url or not isinstance(url, str):
        return False
    try:
        result = requests.utils.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from a URL to a destination path."""
    if not is_valid_url(url):
        logger.warning(f"Invalid URL provided: {url}")
        return False
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_source_verified(source_url: str) -> bool:
    """
    Verify if the source URL belongs to a canonical public data source.
    Validates against known domains for UCI and OpenML.
    """
    if not source_url:
        return False
    
    # Normalize URL to extract domain
    try:
        parsed = requests.utils.urlparse(source_url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        # Check against canonical patterns
        for canonical in CANONICAL_DOMAINS:
            if domain == canonical or domain.endswith('.' + canonical):
                # Specific check for UCI archive paths
                if 'ics.uci.edu' in domain:
                    if '/ml/' in path or '/datasets/' in path:
                        return True
                    # Sometimes just the archive domain is present
                    if 'archive' in domain:
                        return True
            
            if 'openml.org' in domain:
                # OpenML datasets usually have /api/v1/t/... or /d/...
                if '/api/' in path or '/d/' in path or '/t/' in path:
                    return True
                # Direct dataset links
                if 'openml.org' in domain:
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error parsing URL for verification: {source_url}, Error: {e}")
        return False

def get_dataset_info_from_openml(dataset_id: int) -> Optional[Dict[str, Any]]:
    """Fetch dataset metadata from OpenML API."""
    url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and 'oml:data' in data['data']:
            info = data['data']['oml:data']
            return {
                "dataset_id": str(info.get('did', dataset_id)),
                "name": info.get('name', 'unknown'),
                "url": info.get('url', ''),
                "num_rows": int(info.get('number_of_instances', 0)),
                "num_cols": int(info.get('number_of_attributes', 0)),
                "target": info.get('default_target_attribute', None),
                "format": info.get('format', 'ARFF')
            }
    except Exception as e:
        logger.error(f"Failed to fetch info for OpenML dataset {dataset_id}: {e}")
    return None

def fetch_openml_datasets(min_rows: int = 30, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch a list of datasets from OpenML that meet criteria.
    Returns list of metadata dicts.
    """
    # OpenML search API
    search_url = "https://www.openml.org/api/v1/json/data/list/"
    params = {
        "size": max_results * 2, # Fetch more to filter
        "limit": max_results * 2,
        "offset": 0,
        "sort": "id",
        "order": "desc"
    }
    
    datasets = []
    tried = 0
    attempts = 0
    max_attempts = max_results * 10 # Safety break

    while len(datasets) < max_results and attempts < max_attempts:
        params['offset'] = attempts * 10
        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data or 'oml:data' not in data['data']:
                break
            
            for item in data['data']['oml:data']:
                num_inst = int(item.get('number_of_instances', 0))
                if num_inst >= min_rows:
                    datasets.append({
                        "dataset_id": str(item['did']),
                        "name": item['name'],
                        "url": f"https://www.openml.org/d/{item['did']}",
                        "num_rows": num_inst,
                        "num_cols": int(item.get('number_of_attributes', 0)),
                        "target": item.get('default_target_attribute'),
                        "format": item.get('format', 'ARFF'),
                        "source_verified": is_source_verified(item.get('url', ''))
                    })
                    if len(datasets) >= max_results:
                        break
        except Exception as e:
            logger.error(f"Error fetching OpenML list page {attempts}: {e}")
            break
        attempts += 1
    
    if len(datasets) < 50:
        raise ConnectionError(f"Dataset fetch failed: fewer than 50 public datasets found. Retrieved {len(datasets)}.")
    
    return datasets[:max_results]

def process_uci_dataset(dataset_id: str, url: str, dest_dir: Path) -> Optional[Dict[str, Any]]:
    """Process a UCI dataset (simplified placeholder for structure)."""
    # UCI processing is complex due to varied formats; OpenML is primary source here.
    # This function exists to maintain API symmetry if UCI sources are added later.
    logger.warning(f"UCI processing for {dataset_id} not fully implemented in this scope. Skipping.")
    return None

def process_openml_dataset(dataset_info: Dict[str, Any], dest_dir: Path) -> Optional[Dict[str, Any]]:
    """Download and process an OpenML dataset."""
    did = dataset_info['dataset_id']
    url = dataset_info['url']
    file_path = dest_dir / f"dataset_{did}.arff"
    
    # Download the actual data file from OpenML
    # OpenML provides direct download links via API usually, but here we use the main URL
    # For robustness, we might need the specific download endpoint:
    # https://www.openml.org/api/v1/json/data/download/{did}
    download_url = f"https://www.openml.org/api/v1/json/data/download/{did}"
    
    if not download_file(download_url, file_path):
        # Fallback to main URL if download endpoint fails
        if not download_file(url, file_path):
            return None

    checksum = compute_sha256(file_path)
    
    # Verify source again at this stage
    verified = is_source_verified(url)
    if not verified:
        logger.warning(f"Dataset {did} source URL {url} could not be verified against canonical domains.")
    
    return {
        "dataset_id": did,
        "source_url": url,
        "num_rows": dataset_info['num_rows'],
        "num_cols": dataset_info['num_cols'],
        "target_variable": dataset_info.get('target', ''),
        "checksum": checksum,
        "source_verified": verified,
        "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_path": str(file_path)
    }

def initialize_metadata_files(data_dir: Path):
    """Create header rows for metadata CSVs if they don't exist."""
    datasets_file = data_dir / "datasets.csv"
    checksums_file = data_dir / "checksums.csv"
    
    if not datasets_file.exists():
        with open(datasets_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_HEADERS)
            writer.writeheader()
    
    if not checksums_file.exists():
        with open(checksums_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CHECKSUMS_HEADERS)
            writer.writeheader()

def append_to_datasets_csv(data_dir: Path, record: Dict[str, Any]):
    """Append a dataset record to datasets.csv."""
    file_path = data_dir / "datasets.csv"
    with open(file_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_HEADERS)
        # Ensure all keys exist, fill missing with empty string
        row = {k: record.get(k, '') for k in REQUIRED_HEADERS}
        writer.writerow(row)

def append_to_checksums_csv(data_dir: Path, record: Dict[str, Any]):
    """Append a checksum record to checksums.csv."""
    file_path = data_dir / "checksums.csv"
    with open(file_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CHECKSUMS_HEADERS)
        row = {k: record.get(k, '') for k in CHECKSUMS_HEADERS}
        writer.writerow(row)

def update_project_state_artifact_hashes(run_id: str, step: str, data_dir: Path):
    """Update checkpoint state with current artifact counts."""
    datasets_count = 0
    checksums_count = 0
    
    datasets_file = data_dir / "datasets.csv"
    if datasets_file.exists():
        with open(datasets_file, 'r') as f:
            datasets_count = sum(1 for _ in f) - 1 # Subtract header
    
    checksums_file = data_dir / "checksums.csv"
    if checksums_file.exists():
        with open(checksums_file, 'r') as f:
            checksums_count = sum(1 for _ in f) - 1
    
    state = {
        "current_dataset_id": "bulk_download",
        "last_seed": 42,
        "error_counts": {"fetch_errors": 0, "verify_errors": 0},
        "datasets_count": datasets_count,
        "checksums_count": checksums_count
    }
    save_state(run_id, step, state)

def main():
    """Main entry point for downloading and verifying datasets."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    run_id = "T013b_verification_run"
    
    logger.info("Starting dataset download and verification pipeline.")
    initialize_metadata_files(data_dir)
    
    try:
        # Fetch datasets from OpenML
        logger.info("Fetching datasets from OpenML...")
        datasets = fetch_openml_datasets(min_rows=30, max_results=60)
        logger.info(f"Retrieved {len(datasets)} candidate datasets.")
        
        processed_count = 0
        verified_count = 0
        
        for ds_info in datasets:
            logger.info(f"Processing dataset {ds_info['dataset_id']}...")
            result = process_openml_dataset(ds_info, data_dir)
            
            if result:
                # CRITICAL: Verify source URL against canonical patterns
                # The function is_source_verified is called inside process_openml_dataset
                # and the result is stored in 'source_verified'.
                
                if result['source_verified']:
                    verified_count += 1
                else:
                    logger.warning(f"Dataset {result['dataset_id']} failed source verification. Skipping write.")
                    continue
                
                append_to_datasets_csv(data_dir, result)
                append_to_checksums_csv(data_dir, result)
                processed_count += 1
            else:
                logger.error(f"Failed to process dataset {ds_info['dataset_id']}.")
        
        logger.info(f"Pipeline complete. Processed: {processed_count}, Verified: {verified_count}.")
        
        if processed_count < 50:
            # This should ideally be caught earlier, but as a final check
            logger.error(f"Final count {processed_count} is below 50. Raising error.")
            raise ConnectionError(f"Dataset fetch failed: fewer than 50 public datasets found (actual: {processed_count}).")
        
        update_project_state_artifact_hashes(run_id, "download_complete", data_dir)
        
    except ConnectionError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()