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

def download_dataset(url: str, dest_path: str, expected_checksum: Optional[str] = None) -> bool:
    """
    Download a dataset from a URL and validate checksum if provided.
    """
    logger.info(f"Downloading from {url} to {dest_path}")
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as response:
            with open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
        
        if expected_checksum:
            actual = compute_checksum(dest_path)
            if actual != expected_checksum:
                logger.error(f"Checksum mismatch: expected {expected_checksum}, got {actual}")
                return False
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False

def load_datasets_from_raw(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load all CSV/Parquet files from raw_dir.
    Returns a dict of {name: df}.
    """
    datasets = {}
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets

    for file in raw_path.glob("*"):
        if file.suffix in ['.csv', '.parquet']:
            try:
                if file.suffix == '.csv':
                    df = pd.read_csv(file)
                else:
                    df = pd.read_parquet(file)
                datasets[file.stem] = df
                logger.info(f"Loaded {file.name} with shape {df.shape}")
            except Exception as e:
                logger.error(f"Failed to load {file}: {e}")
    return datasets

def ensure_data_exists(raw_dir: str, urls: Dict[str, str]) -> bool:
    """
    Check if data exists, if not, download.
    """
    raw_path = Path(raw_dir)
    raw_path.mkdir(parents=True, exist_ok=True)
    
    for name, url in urls.items():
        file_path = raw_path / f"{name}.csv"
        if not file_path.exists():
            if not download_dataset(url, str(file_path)):
                return False
    return True

def main():
    pass

if __name__ == "__main__":
    main()
