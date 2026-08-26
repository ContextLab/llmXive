import os
import logging
from pathlib import Path
from typing import Tuple, Optional
import requests
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fetch_huggingface_data(repo_id: str, filename: str, output_dir: Path) -> Path:
    """
    Fetches a file from a HuggingFace repository.
    
    Args:
        repo_id: The HuggingFace repository ID (e.g., "username/repo").
        filename: The name of the file to download.
        output_dir: The directory to save the file to.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        Exception: If the download fails or the file is not found.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    # If file already exists, skip download (optional optimization)
    if output_path.exists():
        logger.info(f"File already exists: {output_path}")
        return output_path

    # Construct the direct download URL
    # HuggingFace raw file URL format:
    # https://huggingface.co/{repo_id}/resolve/main/{filename}
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    logger.info(f"Attempting to download from: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded {filename} to {output_path}")
        return output_path
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise FileNotFoundError(f"File not found in repository {repo_id}: {filename}")
        else:
            raise RuntimeError(f"HTTP error during download: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to download {filename} from HuggingFace: {e}")
