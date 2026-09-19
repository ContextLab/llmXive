import os
import sys
import csv
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import requests
import openml
import pandas as pd
from scipy import stats

# Import from project utils to ensure consistency
from code.utils.logging_config import setup_pipeline_logger
from code.utils.checkpointing import save_state, load_state
from code.utils.data_model import Dataset

# Configure logger
logger = setup_pipeline_logger("download_datasets")

# Constants
DATA_DIR = Path("data")
DOWNLOADS_DIR = DATA_DIR / "raw_downloads"
RESULTS_DIR = Path("results")
CHECKPOINT_DIR = RESULTS_DIR / "checkpoints"
DATASETS_CSV = DATA_DIR / "datasets.csv"
CHECKSUMS_CSV = DATA_DIR / "checksums.csv"
STATE_FILE = RESULTS_DIR / "download_state.json"

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = requests.utils.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def download_file(url: str, dest_path: Path, timeout: int = 300) -> bool:
    """
    Download a file from a URL to a destination path.
    Returns True on success, False on failure.
    """
    if not is_valid_url(url):
        logger.warning(f"Invalid URL: {url}")
        return False

    try:
        logger.info(f"Downloading {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Successfully downloaded to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_dataset_info_from_openml(dataset_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a dataset from OpenML.
    Returns a dict with dataset info or None if not found.
    """
    try:
        logger.info(f"Fetching OpenML dataset metadata for ID: {dataset_id}")
        dataset = openml.datasets.get_dataset(dataset_id)
        
        # Extract relevant metadata
        info = {
            "dataset_id": f"openml_{dataset_id}",
            "source": "openml",
            "source_url": dataset.url,
            "name": dataset.name,
            "version": dataset.version,
            "upload_date": dataset.upload_date,
            "number_of_instances": dataset.number_of_instances,
            "number_of_features": dataset.number_of_features,
            "number_of_numeric_features": dataset.number_of_numeric_features,
            "number_of_categorical_features": dataset.number_of_categorical_features,
            "number_of_ignored_features": dataset.number_of_ignored_features,
            "number_of_missing_values": dataset.number_of_missing_values,
            "default_target_attribute": dataset.default_target_attribute,
            "dataset": dataset, # Keep the object for later processing
            "file_path": None # Will be set after download
        }
        return info
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset {dataset_id}: {e}")
        return None

def fetch_openml_datasets(dataset_ids: List[int], max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    Fetch multiple datasets from OpenML by ID.
    Returns a list of dataset info dicts.
    """
    results = []
    for did in dataset_ids:
        info = None
        for attempt in range(max_retries):
            info = get_dataset_info_from_openml(did)
            if info:
                break
            logger.warning(f"Retry {attempt + 1}/{max_retries} for OpenML ID {did}")
            time.sleep(2 ** attempt) # Exponential backoff
        
        if info:
            results.append(info)
        else:
            logger.error(f"Failed to fetch OpenML dataset {did} after {max_retries} retries")
    return results

def initialize_metadata_files():
    """Initialize the metadata CSV files if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DATASETS_CSV.exists():
        with open(DATASETS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "dataset_id", "source", "source_url", "name", "version",
                "sample_size", "num_features", "target_attribute", "file_path", "checksum", "download_date"
            ])
        logger.info(f"Initialized {DATASETS_CSV}")
    
    if not CHECKSUMS_CSV.exists():
        with open(CHECKSUMS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["dataset_id", "checksum", "file_path", "timestamp"])
        logger.info(f"Initialized {CHECKSUMS_CSV}")

def append_to_datasets_csv(dataset_info: Dict[str, Any], checksum: str):
    """Append dataset metadata to the main datasets CSV."""
    with open(DATASETS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            dataset_info.get("dataset_id"),
            dataset_info.get("source"),
            dataset_info.get("source_url"),
            dataset_info.get("name"),
            dataset_info.get("version"),
            dataset_info.get("number_of_instances"),
            dataset_info.get("number_of_features"),
            dataset_info.get("default_target_attribute"),
            dataset_info.get("file_path"),
            checksum,
            time.strftime("%Y-%m-%d %H:%M:%S")
        ])

def append_to_checksums_csv(dataset_id: str, checksum: str, file_path: str):
    """Append checksum info to the checksums CSV."""
    with open(CHECKSUMS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            dataset_id,
            checksum,
            file_path,
            time.strftime("%Y-%m-%d %H:%M:%S")
        ])

def update_project_state_artifact_hashes(checksums: Dict[str, str]):
    """
    Update the project state YAML with artifact hashes.
    Note: This is a simplified implementation. In a real scenario, 
    we would parse and update the YAML file properly.
    """
    state_file = Path("state/projects/PROJ-533-evaluating-the-impact-of-data-transforma.yaml")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Simple append/update logic for demonstration
    # In production, use a proper YAML parser
    content = ""
    if state_file.exists():
        with open(state_file, 'r') as f:
            content = f.read()
    
    # Ensure we have the artifact_hashes section
    if "artifact_hashes:" not in content:
        content += "\nartifact_hashes:\n"
    
    # Append new checksums
    for key, value in checksums.items():
        if f"  {key}:" not in content:
            content += f"  {key}: {value}\n"
    
    with open(state_file, 'w') as f:
        f.write(content)
    logger.info(f"Updated project state in {state_file}")

def process_uci_dataset(dataset_url: str, dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Process a UCI dataset: download, checksum, and log.
    Returns dataset info dict or None on failure.
    """
    try:
        logger.info(f"Processing UCI dataset: {dataset_id}")
        file_name = f"{dataset_id}.csv"
        dest_path = DOWNLOADS_DIR / file_name
        
        if download_file(dataset_url, dest_path):
            checksum = compute_sha256(dest_path)
            
            # Basic metadata extraction (simplified for UCI)
            info = {
                "dataset_id": dataset_id,
                "source": "uci",
                "source_url": dataset_url,
                "name": dataset_id,
                "version": "1",
                "file_path": str(dest_path),
                "checksum": checksum
            }
            
            append_to_datasets_csv(info, checksum)
            append_to_checksums_csv(dataset_id, checksum, str(dest_path))
            
            logger.info(f"Successfully processed UCI dataset {dataset_id} (Checksum: {checksum[:16]}...)")
            return info
        else:
            return None
    except Exception as e:
        logger.error(f"Error processing UCI dataset {dataset_id}: {e}")
        return None

def process_openml_dataset(dataset_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process an OpenML dataset: download, checksum, and log.
    Returns updated dataset info dict or None on failure.
    """
    try:
        dataset_id = dataset_info["dataset_id"]
        logger.info(f"Processing OpenML dataset: {dataset_id}")
        
        # Download the dataset
        dataset_obj = dataset_info.get("dataset")
        if not dataset_obj:
            logger.error(f"No dataset object for {dataset_id}")
            return None
        
        # Get the ARFF file path
        arff_path = dataset_obj.get_data(dataset_format="arff")[0] # Returns (data, features, dataset)
        
        # Convert to CSV for consistency (or keep ARFF if preferred)
        # For this implementation, we'll download the ARFF and compute checksum
        # OpenML API handles caching, so we just need the path
        if hasattr(arff_path, 'read'):
            # If it's a file-like object, save it
            file_name = f"{dataset_id}.arff"
            dest_path = DOWNLOADS_DIR / file_name
            with open(dest_path, 'wb') as f:
                f.write(arff_path.read())
        else:
            dest_path = Path(arff_path)
        
        checksum = compute_sha256(dest_path)
        
        # Update info
        dataset_info["file_path"] = str(dest_path)
        dataset_info["checksum"] = checksum
        
        append_to_datasets_csv(dataset_info, checksum)
        append_to_checksums_csv(dataset_id, checksum, str(dest_path))
        
        logger.info(f"Successfully processed OpenML dataset {dataset_id} (Checksum: {checksum[:16]}...)")
        return dataset_info
    except Exception as e:
        logger.error(f"Error processing OpenML dataset {dataset_info.get('dataset_id')}: {e}")
        return None

def main():
    """
    Main function to download datasets from UCI and OpenML.
    This implementation focuses on OpenML as it's more programmatic.
    """
    logger.info("Starting dataset download pipeline")
    
    # Initialize directories and files
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    initialize_metadata_files()
    
    # Load checkpoint if exists
    state = load_state("download_datasets")
    start_index = state.get("start_index", 0) if state else 0
    logger.info(f"Resuming from index {start_index}")
    
    # List of OpenML dataset IDs to fetch (common datasets)
    # This is a sample list. In production, this could be loaded from a config file.
    openml_ids = [
        1590,  # Adult
        1596,  # Breast Cancer
        1461,  # Wine
        1486,  # Iris
        40984, # Titanic
        41143, # Heart Disease
        41164, # Diabetes
        41165, # Credit Approval
        41169, # Car Evaluation
        41170, # Nursery
        41171, # Hayes Roth
        41172, # Monk's Problems
        41173, # Glass Identification
        41174, # Ionosphere
        41175, # Sonar
        41176, # Soybean
        41177, # Voting
        41178, # Zoo
        41179, # Lymphography
        41180, # Primary Tumor
    ]
    
    # Filter out already processed if resuming
    ids_to_process = openml_ids[start_index:]
    
    if not ids_to_process:
        logger.info("No datasets to process. All done.")
        return
    
    success_count = 0
    fail_count = 0
    
    for i, did in enumerate(ids_to_process):
        try:
            # Fetch metadata
            info = get_dataset_info_from_openml(did)
            if not info:
                fail_count += 1
                continue
            
            # Process the dataset
            result = process_openml_dataset(info)
            if result:
                success_count += 1
            else:
                fail_count += 1
            
            # Update checkpoint after each successful dataset
            save_state("download_datasets", "download_step", {
                "start_index": start_index + i + 1,
                "success_count": success_count,
                "fail_count": fail_count
            })
            
        except Exception as e:
            logger.error(f"Unexpected error processing dataset {did}: {e}")
            fail_count += 1
            # Continue to next dataset
            continue
    
    logger.info(f"Download pipeline completed. Success: {success_count}, Failed: {fail_count}")
    
    # Update project state with checksums
    # Read checksums.csv to get all checksums
    checksums_map = {}
    if CHECKSUMS_CSV.exists():
        with open(CHECKSUMS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                checksums_map[row['dataset_id']] = row['checksum']
    
    if checksums_map:
        update_project_state_artifact_hashes(checksums_map)

if __name__ == "__main__":
    main()