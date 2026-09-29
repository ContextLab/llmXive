import os
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import Optional
import requests
import yaml

from config import get_project_root, get_data_paths
from validators import validate_citations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> dict:
    """Loads a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataset(url: str, metadata_path: str) -> bool:
    """Validates the dataset URL and metadata."""
    result = validate_citations(url, metadata_path)
    return result['success']

def download_bulk_configs(url: str, max_retries: int = 3) -> Path:
    """
    Downloads bulk configurations from a given URL.
    
    Args:
        url: The URL to download from.
        max_retries: Maximum number of retry attempts.
    
    Returns:
        Path to the downloaded file or directory.
    
    Raises:
        FileNotFoundError: If the dataset is inaccessible after retries and no backup exists.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    raw_dir = data_paths['raw']
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = data_paths.get('metadata', project_root / 'data' / 'metadata.yaml')
    
    # Validate URL first
    if not validate_dataset(url, str(metadata_path)):
        logger.warning(f"[DATA_UNAVAILABLE] URL={url} validation failed.")
        # Log to inaccessible manifest
        manifest_path = project_root / 'data' / 'inaccessible_manifest.json'
        manifest_data = []
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
        
        manifest_data.append({
            "url": url,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reason": "validation_failed"
        })
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        # Check backup
        backup_dir = raw_dir / 'backup'
        if backup_dir.exists() and any(backup_dir.iterdir()):
            logger.info("Attempting to load from backup...")
            # Placeholder for backup loading logic
            return backup_dir
        
        raise FileNotFoundError(f"[DATA_UNAVAILABLE] URL={url} is inaccessible and no backup found.")

    # Attempt download with retries
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Downloading from {url} (Attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Determine filename from URL or generate one
            filename = url.split('/')[-1]
            if not filename:
                filename = f"bulk_config_{hashlib.md5(url.encode()).hexdigest()[:8]}.json"
            
            save_path = raw_dir / filename
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded to {save_path}")
            return save_path
            
        except requests.exceptions.RequestException as e:
            attempt += 1
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.error(f"[DATA_UNAVAILABLE] URL={url} attempts={max_retries}")
                # Log to manifest
                manifest_path = project_root / 'data' / 'inaccessible_manifest.json'
                manifest_data = []
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest_data = json.load(f)
                manifest_data.append({
                    "url": url,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "reason": "download_failed"
                })
                with open(manifest_path, 'w') as f:
                    json.dump(manifest_data, f, indent=2)
                
                # Check backup
                backup_dir = raw_dir / 'backup'
                if backup_dir.exists() and any(backup_dir.iterdir()):
                    logger.info("Attempting to load from backup...")
                    return backup_dir
                
                raise FileNotFoundError(f"[DATA_UNAVAILABLE] URL={url} is inaccessible.")
            time.sleep(2 ** attempt) # Exponential backoff

def main():
    """
    Main entry point for the download script.
    """
    # Example usage - in real pipeline, URL comes from config or args
    # This is a placeholder for the script execution
    logger.info("Download module loaded. Use download_bulk_configs(url) to download.")

if __name__ == "__main__":
    main()
