import os
import time
import logging
import shutil
import gc
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from huggingface_hub import HfApi, hf_hub_download, list_repo_files
from huggingface_hub.utils import RepositoryNotFoundError, HfHubHTTPError

from config import get_config, require_hf_token
from utils.logging_config import get_logger, log_download_progress, log_error_summary

logger = get_logger(__name__)

class DownloadError(Exception):
    """Custom exception for data download failures."""
    pass

def exponential_backoff(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate delay with exponential backoff."""
    delay = min(base_delay * (2 ** retry_count), max_delay)
    logger.info("Rate limit hit. Retrying in %.2f seconds (attempt %d)...", delay, retry_count + 1)
    return delay

def download_with_retry(
    repo_id: str,
    filename: str,
    local_dir: Path,
    token: str,
    max_retries: int = 5
) -> Path:
    """
    Download a file from HuggingFace Hub with retry logic.
    
    Args:
        repo_id: HuggingFace repository ID.
        filename: Name of the file to download.
        local_dir: Local directory to save the file.
        token: HuggingFace API token.
        max_retries: Maximum number of retry attempts.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        DownloadError: If download fails after all retries.
    """
    for attempt in range(max_retries):
        try:
            logger.info("Downloading %s from %s (attempt %d/%d)...", filename, repo_id, attempt + 1, max_retries)
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(local_dir),
                token=token,
                local_dir_use_symlinks=False
            )
            logger.info("Successfully downloaded: %s", local_path)
            return Path(local_path)
        except (RepositoryNotFoundError, HfHubHTTPError) as e:
            if attempt == max_retries - 1:
                logger.error("Failed to download %s after %d attempts: %s", filename, max_retries, str(e))
                raise DownloadError(f"Failed to download {filename}: {str(e)}") from e
            
            delay = exponential_backoff(attempt)
            time.sleep(delay)
        except Exception as e:
            logger.error("Unexpected error downloading %s: %s", filename, str(e))
            raise DownloadError(f"Unexpected error downloading {filename}: {str(e)}") from e

def fetch_dataset_metadata(repo_id: str, token: str) -> List[str]:
    """
    Fetch list of files in a HuggingFace repository.
    
    Args:
        repo_id: Repository ID.
        token: API token.
    
    Returns:
        List of filenames in the repository.
    """
    try:
        api = HfApi(token=token)
        files = api.list_repo_files(repo_id=repo_id)
        logger.info("Found %d files in repository %s", len(files), repo_id)
        return files
    except Exception as e:
        logger.error("Failed to fetch metadata for %s: %s", repo_id, str(e))
        raise DownloadError(f"Failed to fetch metadata for {repo_id}") from e

def process_property_files(
    repo_id: str,
    local_dir: Path,
    token: str,
    property_name: str
) -> Dict[str, Path]:
    """
    Download all files for a specific property dataset.
    
    Args:
        repo_id: Repository ID.
        local_dir: Base local directory.
        token: API token.
        property_name: Name of the property (used to create subdirectory).
    
    Returns:
        Dictionary mapping filenames to local paths.
    """
    property_dir = local_dir / property_name
    property_dir.mkdir(parents=True, exist_ok=True)
    
    files = fetch_dataset_metadata(repo_id, token)
    downloaded_files = {}
    
    # Filter for relevant data files (csv, parquet, json)
    relevant_files = [f for f in files if f.endswith(('.csv', '.parquet', '.json', '.tsv'))]
    
    total = len(relevant_files)
    current = 0
    
    for filename in relevant_files:
        current += 1
        log_download_progress(logger, current, total, f"Download {property_name}")
        try:
            local_path = download_with_retry(repo_id, filename, property_dir, token)
            downloaded_files[filename] = local_path
        except DownloadError as e:
            logger.warning("Skipping file %s due to error: %s", filename, str(e))
            continue
    
    log_error_summary(logger, total - len(downloaded_files), f"Download {property_name}")
    return downloaded_files

def download_all_datasets(
    properties: List[Dict[str, str]],
    base_dir: Path,
    token: str
) -> Dict[str, Dict[str, Path]]:
    """
    Download datasets for all specified properties.
    
    Args:
        properties: List of dicts with 'name' and 'repo_id'.
        base_dir: Base directory for downloads.
        token: API token.
    
    Returns:
        Nested dict: {property_name: {filename: local_path}}.
    """
    all_downloads = {}
    total_properties = len(properties)
    
    for idx, prop in enumerate(properties):
        prop_name = prop['name']
        repo_id = prop['repo_id']
        
        logger.info("Processing property %d/%d: %s (Repo: %s)", idx + 1, total_properties, prop_name, repo_id)
        
        try:
            downloaded = process_property_files(repo_id, base_dir, token, prop_name)
            all_downloads[prop_name] = downloaded
            logger.info("Completed download for %s: %d files", prop_name, len(downloaded))
        except Exception as e:
            logger.error("Failed to download dataset for %s: %s", prop_name, str(e))
            # Continue with other properties
            continue
    
    return all_downloads

def main():
    """Main entry point for data download."""
    config = get_config()
    require_hf_token()
    
    raw_dir = config.data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Define datasets to download (example configuration)
    # In a real scenario, this would come from a config file or spec
    datasets = [
        {"name": "formation_energy", "repo_id": "materialsproject/formation_energy"},
        {"name": "band_gap", "repo_id": "materialsproject/band_gap"},
        {"name": "elastic_modulus", "repo_id": "materialsproject/elastic_modulus"},
        # Add more properties as available
    ]
    
    logger.info("Starting data download for %d properties...", len(datasets))
    
    try:
        results = download_all_datasets(datasets, raw_dir, config.hf_token)
        
        total_files = sum(len(files) for files in results.values())
        logger.info("Download complete. Total files downloaded: %d", total_files)
        
        # Log summary
        for prop, files in results.items():
            logger.info("Property %s: %d files", prop, len(files))
            
    except Exception as e:
        logger.critical("Data download pipeline failed: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
