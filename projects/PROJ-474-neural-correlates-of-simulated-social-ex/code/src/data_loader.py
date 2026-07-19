import os
import time
import json
import requests
import tarfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

from src.config import load_config
from src.utils import get_logger, log_exception
from src.exceptions import DataUnavailableError
from src.integrity import update_hashes

def load_openneuro_dataset(dataset_id: str, version: str, output_dir: Path, config: Dict[str, Any], logger: logging.Logger) -> Path:
    """
    Download OpenNeuro dataset with retry logic and checksum verification.
    """
    url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/download"
    # Direct S3 link or tarball
    # For ds000030, we might need a specific mirror or API
    # Using a placeholder URL for the example logic
    s3_url = f"https://s3.amazonaws.com/openneuro.org/ds000030/ds000030.tar.gz"
    
    raw_dir = output_dir / dataset_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    tar_path = raw_dir / f"{dataset_id}.tar.gz"
    
    logger.info(f"Downloading {dataset_id} from {s3_url}...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(s3_url, stream=True)
            response.raise_for_status()
            with open(tar_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            break
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise DataUnavailableError(f"Failed to download dataset after {max_retries} retries: {e}")
            time.sleep(2 ** attempt)
    
    # Extract
    logger.info(f"Extracting {tar_path}...")
    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(path=raw_dir)
    
    # Checksum
    logger.info("Computing checksum...")
    # Assuming update_hashes handles the hashing and state update
    update_hashes([tar_path], config, logger)
    
    # Verify metadata (Inclusion/Exclusion)
    # Placeholder for checking events.tsv files
    events_found = False
    # In real implementation, scan for events.tsv and check trial types
    # For now, assume success if download worked
    if not events_found:
        # Check if we actually found the events
        # If not, raise
        raise DataUnavailableError("Dataset metadata missing Inclusion/Exclusion trial types")

    return raw_dir

def main(config: Dict[str, Any], logger: logging.Logger):
    """Entry point for data loading."""
    dataset_id = config.get('data', {}).get('dataset_id', 'ds000030')
    version = config.get('data', {}).get('version', '1.0.0')
    output_dir = Path(config['paths']['raw_data'])
    
    try:
        load_openneuro_dataset(dataset_id, version, output_dir, config, logger)
        logger.info("Data download and verification completed.")
    except DataUnavailableError as e:
        logger.error(str(e))
        log_exception(logger)
        raise

if __name__ == "__main__":
    config = load_config()
    logger = get_logger()
    main(config, logger)
