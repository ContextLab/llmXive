"""
Utilities for fetching data from HuggingFace Hub.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from huggingface_hub import hf_hub_download, HfApi
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fetch_huggingface_data(
    repo_id: str,
    filename: str,
    local_dir: Path,
    token: Optional[str] = None
) -> str:
    """
    Downloads a specific file from a HuggingFace repository.
    
    Args:
        repo_id: The HuggingFace repository ID (e.g., 'username/repo-name')
        filename: The name of the file to download
        local_dir: The local directory to save the file
        token: Optional authentication token (not needed for public repos)
    
    Returns:
        Path to the downloaded file
    
    Raises:
        FileNotFoundError: If the file does not exist in the repository
        Exception: For other network or download errors
    """
    local_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Downloading {filename} from {repo_id} to {local_dir}")
        
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(local_dir),
            token=token
        )
        
        logger.info(f"Downloaded to: {downloaded_path}")
        return downloaded_path
        
    except Exception as e:
        logger.error(f"Error downloading from HuggingFace: {e}")
        # Re-raise to allow the caller to handle the failure (fail loudly)
        raise
