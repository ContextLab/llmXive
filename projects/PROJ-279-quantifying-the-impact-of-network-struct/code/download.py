"""
Data download and configuration loading module.

Handles fetching MD trajectories from Zenodo/HuggingFace and loading
atomic configurations for processing.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from tqdm import tqdm
import requests
from config.env_config import get_zenodo_url, get_data_dir
from logging_config import get_logger
from models.atomic_config import AtomicConfiguration
from validation_utils import compute_file_checksum, verify_file_integrity

logger = get_logger(__name__)

def download_file(url: str, output_path: Path, expected_checksum: Optional[str] = None) -> Path:
    """
    Download a file from a URL with progress bar and optional checksum verification.
    
    Args:
        url: Download URL
        output_path: Local path to save the file
        expected_checksum: Expected SHA256 checksum (optional)
        
    Returns:
        Path to the downloaded file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {output_path}")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f, tqdm(
        desc=output_path.name,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))
    
    if expected_checksum:
        actual_checksum = compute_file_checksum(output_path)
        if not verify_file_integrity(output_path, expected_checksum, actual_checksum):
            raise ValueError(f"Checksum mismatch for {output_path}")
        logger.info(f"Checksum verified for {output_path}")
    
    return output_path

def load_zenodo_metadata() -> Dict[str, Any]:
    """
    Load metadata about available datasets from Zenodo.
    
    Returns:
        Dictionary containing dataset metadata
    """
    zenodo_url = get_zenodo_url()
    metadata_url = f"{zenodo_url}/metadata.json"
    
    try:
        response = requests.get(metadata_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Could not fetch metadata from {metadata_url}: {e}")
        # Return default metadata if fetch fails
        return {
            "datasets": [
                {
                    "id": "as-si-trajectories-v1",
                    "name": "Amorphous Silicon Trajectories",
                    "files": [
                        {
                            "name": "configs.json",
                            "url": f"{zenodo_url}/configs.json",
                            "checksum": None,
                            "description": "Atomic configurations in JSON format"
                        }
                    ]
                }
            ]
        }

def download_configs(metadata: Dict[str, Any], raw_dir: Path) -> Path:
    """
    Download configuration files based on metadata.
    
    Args:
        metadata: Dataset metadata dictionary
        raw_dir: Directory to save raw data
        
    Returns:
        Path to the downloaded configurations file
    """
    if not metadata.get("datasets"):
        raise ValueError("No datasets found in metadata")
    
    # Assume first dataset is the one we want
    dataset = metadata["datasets"][0]
    
    for file_info in dataset.get("files", []):
        if file_info["name"] == "configs.json":
            url = file_info["url"]
            checksum = file_info.get("checksum")
            output_path = raw_dir / "configs.json"
            
            if not output_path.exists():
                download_file(url, output_path, checksum)
            else:
                logger.info(f"Configs already exist at {output_path}")
            
            return output_path
    
    raise FileNotFoundError("configs.json not found in dataset metadata")

def load_configurations_from_raw(
    raw_dir: Path, 
    config_ids: Optional[List[str]] = None
) -> List[AtomicConfiguration]:
    """
    Load atomic configurations from raw data directory.
    
    Args:
        raw_dir: Directory containing raw configuration data
        config_ids: Optional list of specific config IDs to load
        
    Returns:
        List of AtomicConfiguration objects
    """
    configs_path = raw_dir / "configs.json"
    
    if not configs_path.exists():
        # Try to download if not exists
        metadata = load_zenodo_metadata()
        download_configs(metadata, raw_dir)
    
    with open(configs_path, 'r') as f:
        all_configs_data = json.load(f)
    
    configs = []
    for config_data in all_configs_data:
        # Filter by config_ids if specified
        if config_ids and config_data['config_id'] not in config_ids:
            continue
        
        try:
            config = AtomicConfiguration(
                config_id=config_data['config_id'],
                coordinates=np.array(config_data['coordinates']),
                species=config_data['species'],
                source=config_data.get('source', 'unknown'),
                system_size=len(config_data['species']),
                metadata=config_data.get('metadata', {})
            )
            configs.append(config)
        except Exception as e:
            logger.error(f"Failed to load config {config_data.get('config_id', 'unknown')}: {e}")
            continue
    
    logger.info(f"Loaded {len(configs)} configurations from {configs_path}")
    return configs

def main():
    """
    Main entry point for data download.
    
    Downloads MD trajectories from Zenodo and saves to data/raw/
    """
    setup_logging()
    
    raw_dir = get_data_dir() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading data to {raw_dir}")
    
    # Download metadata
    metadata = load_zenodo_metadata()
    
    # Download configurations
    configs_path = download_configs(metadata, raw_dir)
    
    logger.info(f"Download complete. Configurations saved to {configs_path}")

if __name__ == "__main__":
    main()
