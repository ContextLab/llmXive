import json
import logging
import os
import hashlib
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import requests
from tqdm import tqdm

from models.atomic_config import AtomicConfiguration
from config.env_config import get_zenodo_url, get_data_dir, get_config
from logging_config import get_logger
from validation_utils import compute_file_checksum

logger = get_logger(__name__)

def download_file(url: str, dest_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Download a file from URL to dest_path with optional checksum verification.
    Returns True on success, raises exception on failure.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        if expected_checksum:
            actual_checksum = compute_file_checksum(dest_path)
            if actual_checksum != expected_checksum:
                raise ValueError(
                    f"Checksum mismatch for {dest_path}. "
                    f"Expected: {expected_checksum}, Got: {actual_checksum}"
                )
            logger.info(f"Checksum verified for {dest_path}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def load_zenodo_metadata() -> Dict[str, Any]:
    """
    Load metadata about available datasets from Zenodo/HuggingFace.
    This assumes a metadata file is available or fetched from a known URL.
    For this implementation, we assume a local metadata file exists in data/raw/metadata.json
    or we fetch it from a configured URL.
    """
    # In a real scenario, this might fetch from Zenodo API or a local manifest.
    # Here we simulate loading a manifest that describes the files to download.
    config = get_config()
    metadata_url = config.get('metadata_url')
    
    if metadata_url:
        # Fetch metadata
        try:
            resp = requests.get(metadata_url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch metadata from {metadata_url}: {e}")
            raise
    else:
        # Fallback to local file if URL not set
        metadata_path = get_data_dir() / "raw" / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError("No metadata URL configured and local metadata.json not found.")

def download_configs() -> List[Path]:
    """
    Download all configuration files listed in the metadata.
    Returns list of paths to downloaded files.
    """
    metadata = load_zenodo_metadata()
    raw_dir = get_data_dir() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    
    # Assume metadata has a list of files with urls and checksums
    files_to_download = metadata.get('files', [])
    
    if not files_to_download:
        logger.warning("No files found in metadata to download.")
        return []
    
    for file_info in files_to_download:
        url = file_info['url']
        filename = file_info['filename']
        checksum = file_info.get('checksum')
        
        dest_path = raw_dir / filename
        
        if dest_path.exists():
            logger.info(f"File {filename} already exists. Skipping download.")
            # Optionally verify checksum if exists
            if checksum:
                if compute_file_checksum(dest_path) != checksum:
                    logger.warning(f"Existing file {filename} has mismatched checksum. Re-downloading.")
                    dest_path.unlink()
                else:
                    downloaded_files.append(dest_path)
                    continue
            else:
                downloaded_files.append(dest_path)
                continue
        
        try:
            download_file(url, dest_path, checksum)
            downloaded_files.append(dest_path)
        except Exception as e:
            logger.error(f"Skipping {filename} due to error: {e}")
            # Fail loudly as per constraints
            raise e
    
    return downloaded_files

def load_configurations_from_raw() -> List[AtomicConfiguration]:
    """
    Load AtomicConfiguration objects from the downloaded raw files.
    This function assumes the raw files are in a format that can be parsed
    into AtomicConfiguration (e.g., XYZ, CIF, or custom JSON).
    For this implementation, we assume a simple JSON format for demonstration.
    """
    raw_dir = get_data_dir() / "raw"
    configs = []
    
    # Look for .json files in raw directory (adjust extension as needed)
    for file_path in raw_dir.glob("*.json"):
        if file_path.name == "metadata.json":
            continue
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Map JSON fields to AtomicConfiguration
            # Assuming the JSON has: id, positions, atomic_numbers, thermal_conductivity, source
            cfg = AtomicConfiguration(
                id=data['id'],
                positions=np.array(data['positions']),
                atomic_numbers=data['atomic_numbers'],
                thermal_conductivity=data.get('thermal_conductivity'),
                source=data.get('source', 'unknown'),
                size=data.get('size', len(data['positions']))
            )
            configs.append(cfg)
            logger.info(f"Loaded configuration {cfg.id} from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            # Fail loudly
            raise e
    
    if not configs:
        logger.warning("No configurations found in raw directory.")
    
    return configs

def main():
    """
    Entry point for T014: Download and verify trajectories.
    """
    logger.info("Starting T014: Download Configurations")
    try:
        downloaded = download_configs()
        logger.info(f"Downloaded {len(downloaded)} files.")
        
        # Optionally load them to verify structure
        configs = load_configurations_from_raw()
        logger.info(f"Loaded {len(configs)} configurations from raw files.")
        
    except Exception as e:
        logger.error(f"Download process failed: {e}")
        return 1
    
    return 0

# Import numpy locally to avoid global import if not used in main logic
import numpy as np
