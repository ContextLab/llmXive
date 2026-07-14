"""
Download datasets from UCI and OpenML repositories.

This script fetches real-world datasets, logs their URLs, computes SHA-256 checksums,
and stores raw data files in data/raw/. It also updates the datasets.csv and checksums.csv
metadata files.
"""
import os
import sys
import csv
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
import pandas as pd
from scipy import stats

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checkpointing import (
    ensure_checkpoint_dir,
    compute_file_hash,
    get_checkpoint_path,
    save_checkpoint,
    load_checkpoint,
    has_checkpoint,
    delete_checkpoint
)
from utils.logging_config import setup_pipeline_logger

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATASETS_CSV = PROJECT_ROOT / "data" / "datasets.csv"
CHECKSUMS_CSV = PROJECT_ROOT / "data" / "checksums.csv"
CHECKPOINT_DIR = PROJECT_ROOT / "results" / "checkpoints"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ensure_checkpoint_dir(CHECKPOINT_DIR)

# Setup logger
logger = setup_pipeline_logger("download_datasets", PROJECT_ROOT / "results" / "pipeline.log")

# OpenML API configuration
OPENML_API_URL = "https://www.openml.org/api/v1/json/data/list"
UCI_DATASETS = [
    # Using a curated list of known UCI dataset URLs for reliability
    {
        "name": "iris",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        "description": "Iris Flower Dataset"
    },
    {
        "name": "wine",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "description": "Wine Recognition Dataset"
    },
    {
        "name": "breast-cancer-wisconsin",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data",
        "description": "Breast Cancer Wisconsin Dataset"
    },
    {
        "name": "hepatitis",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/hepatitis/hepatitis.data",
        "description": "Hepatitis Dataset"
    },
    {
        "name": "heart-statlog",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/heart/heart.dat",
        "description": "Statlog Heart Dataset"
    },
    {
        "name": "vehicle",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/vehicle/vehicle.csv",
        "description": "Vehicle Silhouettes Dataset"
    },
    {
        "name": "sonar",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/undocumented/connectionist-bench/sonar/sonar.all-data",
        "description": "Sonar Dataset"
    },
    {
        "name": "seeds",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00236/seeds_dataset.txt",
        "description": "Seeds Dataset"
    },
    {
        "name": "concrete",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/concrete_data.xls",
        "description": "Concrete Compressive Strength"
    },
    {
        "name": "bank",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank.zip",
        "description": "Bank Marketing Dataset"
    }
]

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid and accessible."""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from URL to dest_path."""
    try:
        logger.info(f"Downloading from {url} to {dest_path}")
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded {dest_path.name}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_dataset_info_from_openml(dataset_id: int) -> Optional[Dict[str, Any]]:
    """Fetch dataset metadata from OpenML API."""
    try:
        url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('data_set_description', {})
    except Exception as e:
        logger.warning(f"Could not fetch metadata for OpenML dataset {dataset_id}: {e}")
        return None

def fetch_openml_datasets(count: int = 40) -> List[Dict[str, Any]]:
    """Fetch a list of datasets from OpenML."""
    datasets = []
    try:
        # Fetch datasets with numeric features
        params = {
            'limit': count,
            'sort': 'downloads',
            'order': 'desc'
        }
        response = requests.get(OPENML_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        for item in data.get('data', []):
            dataset_info = {
                'dataset_id': item.get('did'),
                'name': item.get('name'),
                'url': f"https://www.openml.org/api/v1/json/data/download/{item.get('did')}",
                'description': item.get('description', 'No description'),
                'source': 'openml'
            }
            datasets.append(dataset_info)
    except Exception as e:
        logger.error(f"Failed to fetch OpenML datasets: {e}")
    
    return datasets

def initialize_metadata_files():
    """Initialize datasets.csv and checksums.csv if they don't exist."""
    datasets_headers = ['dataset_id', 'source_url', 'sample_size', 'continuous_vars', 
                      'group_labels', 'excluded_reason']
    checksums_headers = ['dataset_id', 'sha256_hash']
    
    if not DATASETS_CSV.exists():
        with open(DATASETS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(datasets_headers)
        logger.info(f"Created {DATASETS_CSV}")
    
    if not CHECKSUMS_CSV.exists():
        with open(CHECKSUMS_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(checksums_headers)
        logger.info(f"Created {CHECKSUMS_CSV}")

def append_to_datasets_csv(dataset_info: Dict[str, Any]):
    """Append dataset metadata to datasets.csv."""
    with open(DATASETS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            dataset_info.get('dataset_id'),
            dataset_info.get('source_url'),
            dataset_info.get('sample_size', ''),
            dataset_info.get('continuous_vars', ''),
            dataset_info.get('group_labels', ''),
            dataset_info.get('excluded_reason', '')
        ])

def append_to_checksums_csv(dataset_id: str, sha256_hash: str):
    """Append checksum to checksums.csv."""
    with open(CHECKSUMS_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([dataset_id, sha256_hash])

def process_uci_dataset(dataset_info: Dict[str, Any], run_id: str):
    """Process a single UCI dataset."""
    dataset_name = dataset_info['name']
    url = dataset_info['url']
    dataset_id = f"uci_{dataset_name}"
    
    # Check checkpoint
    checkpoint_path = get_checkpoint_path(CHECKPOINT_DIR, run_id, dataset_id)
    if has_checkpoint(checkpoint_path):
        logger.info(f"Skipping {dataset_name} - already processed")
        return True
    
    # Download file
    dest_filename = f"{dataset_id}.csv"
    dest_path = DATA_RAW_DIR / dest_filename
    
    if not download_file(url, dest_path):
        logger.warning(f"Failed to download {dataset_name}")
        return False
    
    # Compute checksum
    sha256_hash = compute_sha256(dest_path)
    
    # Try to load and get basic info
    try:
        if dest_path.suffix == '.xls' or dest_path.suffix == '.xlsx':
            df = pd.read_excel(dest_path)
        elif dest_path.suffix == '.zip':
            # For zip files, we need to handle extraction
            logger.warning(f"Zip file detected for {dataset_name}, skipping detailed processing")
            df = None
        else:
            # Try to infer delimiter
            df = pd.read_csv(dest_path, sep=None, engine='python')
        
        sample_size = len(df)
        continuous_vars = df.select_dtypes(include=['number']).columns.tolist()
        group_labels = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        dataset_info['sample_size'] = sample_size
        dataset_info['continuous_vars'] = len(continuous_vars)
        dataset_info['group_labels'] = len(group_labels)
    except Exception as e:
        logger.warning(f"Could not process {dataset_name} metadata: {e}")
        dataset_info['sample_size'] = 0
        dataset_info['continuous_vars'] = 0
        dataset_info['group_labels'] = 0
    
    # Save metadata
    append_to_checksums_csv(dataset_id, sha256_hash)
    append_to_datasets_csv(dataset_info)
    
    # Save checkpoint
    save_checkpoint(checkpoint_path, {'dataset_id': dataset_id, 'status': 'completed'})
    logger.info(f"Completed processing {dataset_name}")
    
    return True

def process_openml_dataset(dataset_info: Dict[str, Any], run_id: str):
    """Process a single OpenML dataset."""
    dataset_id = str(dataset_info['dataset_id'])
    url = dataset_info['url']
    dataset_name = dataset_info['name']
    
    # Check checkpoint
    checkpoint_path = get_checkpoint_path(CHECKPOINT_DIR, run_id, f"openml_{dataset_id}")
    if has_checkpoint(checkpoint_path):
        logger.info(f"Skipping OpenML dataset {dataset_name} - already processed")
        return True
    
    # Download file
    dest_filename = f"openml_{dataset_id}.arff"
    dest_path = DATA_RAW_DIR / dest_filename
    
    if not download_file(url, dest_path):
        logger.warning(f"Failed to download OpenML dataset {dataset_name}")
        return False
    
    # Compute checksum
    sha256_hash = compute_sha256(dest_path)
    
    # Try to get metadata from OpenML
    meta_info = get_dataset_info_from_openml(int(dataset_id))
    if meta_info:
        dataset_info['sample_size'] = meta_info.get('number_of_instances', 0)
        dataset_info['continuous_vars'] = meta_info.get('number_of_numeric_attributes', 0)
        dataset_info['group_labels'] = meta_info.get('number_of_nominal_attributes', 0)
    
    # Save metadata
    append_to_checksums_csv(f"openml_{dataset_id}", sha256_hash)
    append_to_datasets_csv(dataset_info)
    
    # Save checkpoint
    save_checkpoint(checkpoint_path, {'dataset_id': f"openml_{dataset_id}", 'status': 'completed'})
    logger.info(f"Completed processing OpenML dataset {dataset_name}")
    
    return True

def main():
    """Main function to download and process datasets."""
    logger.info("Starting dataset download pipeline")
    
    # Initialize metadata files
    initialize_metadata_files()
    
    # Generate run ID
    run_id = f"download_{int(time.time())}"
    
    # Process UCI datasets
    uci_count = 0
    for dataset in UCI_DATASETS:
        if process_uci_dataset(dataset, run_id):
            uci_count += 1
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    logger.info(f"Processed {uci_count} UCI datasets")
    
    # Fetch and process OpenML datasets
    openml_datasets = fetch_openml_datasets(count=40)
    openml_count = 0
    for dataset in openml_datasets:
        if process_openml_dataset(dataset, run_id):
            openml_count += 1
        time.sleep(1)
    
    logger.info(f"Processed {openml_count} OpenML datasets")
    logger.info(f"Total datasets processed: {uci_count + openml_count}")
    
    # Log final state
    logger.info("Dataset download pipeline completed")
    
    return uci_count + openml_count

if __name__ == "__main__":
    main()
