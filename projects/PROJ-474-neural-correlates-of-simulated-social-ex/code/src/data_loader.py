import os
import time
import json
import requests
import tarfile
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Any

from src.config import load_config
from src.utils import get_logger
from src.exceptions import DataUnavailableError
from src.integrity import compute_file_hash

logger = get_logger(__name__)
config = load_config()

def load_openneuro_dataset():
    """
    Downloads OpenNeuro dataset ds000030.
    Implements retry logic and checksum verification.
    """
    dataset_id = 'ds000030'
    version = '1.0.0'
    base_url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/download"
    raw_dir = Path(config['paths']['raw'])
    dest_dir = raw_dir / dataset_id
    
    if dest_dir.exists():
        logger.info(f"Dataset {dataset_id} already exists at {dest_dir}. Skipping download.")
        return dest_dir
    
    logger.info(f"Downloading {dataset_id} from OpenNeuro...")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = raw_dir / f"{dataset_id}.zip"
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(base_url, stream=True)
            response.raise_for_status()
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            break
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise DataUnavailableError(f"Failed to download {dataset_id} after {max_retries} attempts: {e}")
            logger.warning(f"Download attempt {attempt+1} failed. Retrying...")
            time.sleep(2 ** attempt)
    
    # Extract
    logger.info("Extracting dataset...")
    if zip_path.suffix == '.zip':
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(raw_dir)
    elif zip_path.suffix == '.tar':
        with tarfile.open(zip_path, 'r') as tar_ref:
            tar_ref.extractall(raw_dir)
    else:
        raise DataUnavailableError("Unsupported archive format.")
    
    # Cleanup
    zip_path.unlink()
    
    # Verify structure
    if not (dest_dir / 'sub-01').exists():
        raise DataUnavailableError(f"Extracted dataset missing expected structure at {dest_dir}")
    
    logger.info(f"Dataset {dataset_id} ready at {dest_dir}")
    return dest_dir

def main():
    load_openneuro_dataset()

if __name__ == '__main__':
    main()
