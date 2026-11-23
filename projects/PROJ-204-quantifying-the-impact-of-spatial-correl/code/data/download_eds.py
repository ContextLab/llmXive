"""
Module for downloading EDS maps from verified sources.

This module implements the conditional download logic for Task T011.
It checks the feasibility status (T010) and downloads data from the
verified URL (Zenodo) if available.
"""
import os
import sys
import logging
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Output directory for raw data
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

def load_feasibility_status() -> Dict[str, Any]:
    """
    Load the feasibility status from T010.
    
    Returns:
        Dict containing status and URL if successful.
    
    Raises:
        FileNotFoundError: If the feasibility status file is missing.
        ValueError: If the status indicates failure.
    """
    status_path = PROJECT_ROOT / "state" / "data_feasibility_status.yaml"
    
    if not status_path.exists():
        raise FileNotFoundError(
            f"Feasibility status file not found at {status_path}. "
            "Please ensure T010 has been completed successfully."
        )
    
    with open(status_path, 'r') as f:
        status = yaml.safe_load(f)
    
    if status.get('status') != 'success':
        raise ValueError(
            f"Feasibility check failed. Status: {status.get('status')}. "
            "Cannot proceed with download without a verified source."
        )
    
    return status

def download_file(url: str, output_path: Path) -> bool:
    """
    Download a file from a URL to the specified output path.
    
    Args:
        url: The URL to download from.
        output_path: The local path to save the file.
    
    Returns:
        True if download was successful, False otherwise.
    
    Raises:
        requests.RequestException: If the download fails.
    """
    logger.info(f"Downloading from {url} to {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Write in chunks to handle large files
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded {output_path.name}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def download_from_zenodo(zenodo_url: str, dataset_id: str) -> Dict[str, Path]:
    """
    Download EDS maps from Zenodo.
    
    Args:
        zenodo_url: The base URL or specific file URL from Zenodo.
        dataset_id: Identifier for the dataset (used for logging/naming).
    
    Returns:
        Dict mapping sample IDs to their downloaded file paths.
    """
    downloaded_files = {}
    
    # For this implementation, we assume the Zenodo URL points to a specific
    # file or a zip archive containing the EDS maps.
    # In a real scenario, we would parse the Zenodo API response to get
    # individual file URLs.
    
    filename = f"eds_maps_{dataset_id}.zip"
    output_path = RAW_DATA_DIR / filename
    
    try:
        download_file(zenodo_url, output_path)
        downloaded_files[dataset_id] = output_path
    except Exception as e:
        logger.error(f"Failed to download dataset {dataset_id}: {e}")
        # Re-raise to ensure the pipeline fails loudly
        raise
    
    return downloaded_files

def main():
    """
    Main entry point for the download script.
    
    This function:
    1. Loads the feasibility status from T010.
    2. If successful, downloads EDS maps from the verified URL.
    3. Saves raw files to data/raw/.
    4. Logs the results.
    """
    logger.info("Starting T011: Conditional Download of EDS Maps")
    
    # Ensure raw data directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load feasibility status
        status = load_feasibility_status()
        logger.info(f"Feasibility check passed. Verified URL: {status.get('verified_url')}")
        
        # Download from the verified URL
        verified_url = status.get('verified_url')
        dataset_id = status.get('dataset_id', 'default_dataset')
        
        downloaded = download_from_zenodo(verified_url, dataset_id)
        
        # Log success
        logger.info(f"Successfully downloaded {len(downloaded)} dataset(s):")
        for sample_id, path in downloaded.items():
            logger.info(f"  {sample_id}: {path}")
        
        # Write download manifest
        manifest_path = RAW_DATA_DIR / "download_manifest.json"
        manifest_data = {
            "dataset_id": dataset_id,
            "source_url": verified_url,
            "downloaded_files": {k: str(v) for k, v in downloaded.items()},
            "status": "success"
        }
        
        import json
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Download manifest written to {manifest_path}")
        logger.info("T011 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Feasibility status not found: {e}")
        logger.info("T011 SKIPPED: T010 has not been completed successfully.")
        # Create a skip manifest
        skip_manifest_path = RAW_DATA_DIR / "download_manifest.json"
        import json
        with open(skip_manifest_path, 'w') as f:
            json.dump({
                "status": "skipped",
                "reason": str(e)
            }, f, indent=2)
        sys.exit(0)
        
    except ValueError as e:
        logger.error(f"Feasibility check failed: {e}")
        logger.info("T011 SKIPPED: No verified source available.")
        # Create a skip manifest
        skip_manifest_path = RAW_DATA_DIR / "download_manifest.json"
        import json
        with open(skip_manifest_path, 'w') as f:
            json.dump({
                "status": "skipped",
                "reason": str(e)
            }, f, indent=2)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Download failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()