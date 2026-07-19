import os
import time
import logging
import shutil
import gc
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from huggingface_hub import HfApi, hf_hub_download, list_repo_files
from config import get_config, require_hf_token, require_data_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

class DownloadError(Exception):
    """Custom exception for download failures."""
    pass

def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """
    Calculate delay time using exponential backoff with jitter.
    
    Args:
        attempt: The current retry attempt number (0-indexed).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
    
    Returns:
        Delay time in seconds.
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    return delay

def download_with_retry(
    repo_id: str,
    filename: str,
    local_dir: str,
    max_retries: int = 5
) -> str:
    """
    Download a file from HuggingFace Hub with retry logic.
    
    Args:
        repo_id: HuggingFace repository ID.
        filename: Name of the file to download.
        local_dir: Local directory to save the file.
        max_retries: Maximum number of retry attempts.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        DownloadError: If download fails after all retries.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to download {filename} from {repo_id} (attempt {attempt + 1}/{max_retries})")
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=local_dir,
                force_download=False
            )
            logger.info(f"Successfully downloaded {filename} to {local_path}")
            return local_path
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to download {filename} after {max_retries} attempts: {e}")
                raise DownloadError(f"Download failed for {filename}: {e}")
            delay = exponential_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    raise DownloadError(f"Download failed for {filename} after {max_retries} attempts")

def fetch_dataset_metadata(repo_id: str) -> Dict[str, Any]:
    """
    Fetch metadata about a dataset repository.
    
    Args:
        repo_id: HuggingFace repository ID.
    
    Returns:
        Dictionary containing repository metadata.
    """
    try:
        api = HfApi()
        info = api.repo_info(repo_id=repo_id, repo_type="dataset")
        logger.info(f"Fetched metadata for {repo_id}: {info.id}")
        return {
            "id": info.id,
            "sha": info.sha,
            "last_modified": info.last_modified,
            "siblings": [s.rfilename for s in info.siblings]
        }
    except Exception as e:
        logger.error(f"Failed to fetch metadata for {repo_id}: {e}")
        raise DownloadError(f"Metadata fetch failed for {repo_id}: {e}")

def process_property_files(
    base_dir: Path,
    property_name: str,
    file_patterns: List[str]
) -> List[Path]:
    """
    Locate and validate property-specific files in the downloaded data.
    
    Args:
        base_dir: Base directory containing the downloaded data.
        property_name: Name of the property (used for logging).
        file_patterns: List of file patterns to match.
    
    Returns:
        List of paths to matching files.
    """
    matching_files = []
    for pattern in file_patterns:
        files = list(base_dir.glob(pattern))
        if files:
            logger.info(f"Found {len(files)} file(s) matching '{pattern}' for {property_name}")
            matching_files.extend(files)
        else:
            logger.warning(f"No files found matching '{pattern}' for {property_name}")
    
    return matching_files

def download_all_datasets(
    data_dir: Path,
    datasets_config: Dict[str, Dict[str, Any]]
) -> Dict[str, List[Path]]:
    """
    Download all configured datasets.
    
    Args:
        data_dir: Root data directory.
        datasets_config: Configuration dictionary mapping property names to dataset details.
    
    Returns:
        Dictionary mapping property names to lists of downloaded file paths.
    """
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files: Dict[str, List[Path]] = {}
    
    for prop_name, config in datasets_config.items():
        repo_id = config.get("repo_id")
        files = config.get("files", [])
        
        if not repo_id:
            logger.error(f"Missing repo_id for property {prop_name}")
            continue
        
        logger.info(f"Downloading data for property: {prop_name}")
        prop_dir = raw_dir / prop_name
        prop_dir.mkdir(parents=True, exist_ok=True)
        
        prop_files = []
        for file_name in files:
            try:
                local_path = download_with_retry(repo_id, file_name, str(prop_dir))
                prop_files.append(Path(local_path))
            except DownloadError as e:
                logger.error(f"Skipping {prop_name} due to download error: {e}")
                break  # Stop processing this property if one file fails
        
        if prop_files:
            downloaded_files[prop_name] = prop_files
            logger.info(f"Completed download for {prop_name}: {len(prop_files)} files")
        else:
            logger.error(f"Failed to download any files for {prop_name}")
        
        # Garbage collection between properties to manage memory
        gc.collect()
    
    return downloaded_files

def main():
    """
    Main entry point for data download.
    """
    logger.info("Starting data download process")
    
    try:
        config = get_config()
        data_dir = Path(require_data_dir(config))
        
        # Example configuration - in real usage, this might come from a config file
        # or be derived from the project specification
        datasets_config = {
            "formation_energy": {
                "repo_id": "materialsvirtuallab/mp-formulation",
                "files": ["formation_energy.csv"]
            },
            "band_gap": {
                "repo_id": "materialsvirtuallab/mp-formulation",
                "files": ["band_gap.csv"]
            }
        }
        
        downloaded = download_all_datasets(data_dir, datasets_config)
        
        if downloaded:
            logger.info(f"Successfully downloaded data for {len(downloaded)} properties")
            for prop, files in downloaded.items():
                logger.info(f"  - {prop}: {len(files)} files")
        else:
            logger.warning("No datasets were successfully downloaded")
            
    except Exception as e:
        logger.error(f"Data download failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Data download process completed")

if __name__ == "__main__":
    main()
