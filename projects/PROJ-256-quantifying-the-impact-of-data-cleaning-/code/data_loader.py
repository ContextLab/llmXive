import os
import json
import logging
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from urllib.request import urlopen, Request
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

def compute_checksum(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(url: str, output_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Download a dataset from a URL and validate checksum.
    """
    logger.info(f"Downloading {url} to {output_path}")
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as response:
            with open(output_path, 'wb') as out_file:
                out_file.write(response.read())
        
        if expected_checksum:
            actual_checksum = compute_checksum(output_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {output_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
                return False
            else:
                logger.info(f"Checksum validated for {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def load_datasets_from_raw(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV datasets from the raw directory.
    """
    datasets = {}
    csv_files = list(Path(raw_dir).glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {raw_dir}")
        return datasets
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            datasets[csv_file.stem] = df
            logger.info(f"Loaded {csv_file.stem} with {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {csv_file}: {e}")
    
    return datasets

def ensure_data_exists(raw_dir: str, urls: Dict[str, str], checksums: Dict[str, str]) -> bool:
    """
    Ensure data exists in raw_dir, downloading if necessary.
    """
    Path(raw_dir).mkdir(parents=True, exist_ok=True)
    
    for name, url in urls.items():
        filepath = os.path.join(raw_dir, f"{name}.csv")
        if not os.path.exists(filepath):
            if not download_dataset(url, filepath, checksums.get(name)):
                return False
    return True

def main():
    pass

if __name__ == "__main__":
    main()
