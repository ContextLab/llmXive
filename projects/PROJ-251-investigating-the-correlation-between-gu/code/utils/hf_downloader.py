"""
Helper module for fetching pre-processed data from HuggingFace.
Implements the logic for Strategy A (T011a).
"""
import os
import logging
from pathlib import Path
from typing import Tuple

import requests

from utils.logging_config import get_logger
from utils.config import get_raw_path

def fetch_huggingface_data(output_dir: Path) -> Tuple[Path, Path]:
    """
    Fetch pre-processed OTU table and metadata from HuggingFace.
    Verified Source: biothings/srp053178_processed
    
    Args:
        output_dir: Directory to save files.
        
    Returns:
        Tuple of (otu_table_path, metadata_path)
        
    Raises:
        FileNotFoundError: If the dataset is not available or download fails.
    """
    logger = get_logger(__name__)
    
    # Verified source URL
    base_url = "https://huggingface.co/datasets/biothings/srp053178_processed/resolve/main"
    files = {
        "otutable.csv": "otutable.csv",
        "metadata.csv": "metadata.csv"
    }
    
    otu_path = output_dir / "otutable.csv"
    meta_path = output_dir / "metadata.csv"
    
    logger.info("Attempting to fetch pre-processed data from HuggingFace (biothings/srp053178_processed)...")
    
    for name, fname in files.items():
        url = f"{base_url}/{fname}"
        try:
            logger.debug(f"Downloading {fname} from {url}")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            with open(output_dir / name, 'wb') as f:
                f.write(response.content)
            logger.info(f"Successfully downloaded {name}")
        except Exception as e:
            logger.error(f"Failed to download {name} from {url}: {e}")
            raise FileNotFoundError(f"Strategy A failed: Could not retrieve {name} from HuggingFace. Error: {e}")
    
    return otu_path, meta_path