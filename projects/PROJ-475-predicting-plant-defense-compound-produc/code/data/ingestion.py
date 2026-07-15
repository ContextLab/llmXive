"""
Data Ingestion Module for Plant Defense Compound Prediction.

Handles fetching genomic, environmental, and compound data from verified URLs
or generating deterministic mock data for CI/testing when URLs are unavailable.
"""
import json
import os
import sys
import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd

# Local imports
from config import get_config
from utils.io import check_disk_space, DiskSpaceError
from utils.logging import get_module_logger
from data.mock_generator import generate_mock_compound_data

logger = get_module_logger(__name__)
config = get_config()

# Output paths as per task specification
OUTPUT_COMPOUND_DATA = Path("data/raw/compound_data.json")

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def save_data(data: Union[Dict, List], output_path: Path) -> None:
    """
    Save data to a JSON file with proper encoding for numpy types.

    Args:
        data: Data to save (dict or list)
        output_path: Path to save the file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, cls=NumpyEncoder)
    logger.info(f"Data saved to {output_path}")

def fetch_compound_data(url: str) -> Dict[str, Any]:
    """
    Fetch defense compound profiles from a verified URL (ChemBank/PhenolExplorer).

    Args:
        url: The verified URL to fetch data from.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        requests.RequestException: If the fetch fails.
    """
    logger.info(f"Attempting to fetch compound data from: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def run_compound_ingestion() -> Dict[str, Any]:
    """
    Execute the defense compound data ingestion pipeline.

    Logic:
    1. Check if a verified URL for compound data exists in config.
    2. If yes, attempt to fetch. If fetch fails, log error and fall back to mock.
    3. If no verified URL, generate mock data.
    4. Verify disk space before writing.
    5. Save to data/raw/compound_data.json.

    Returns:
        The loaded/generated compound data.
    """
    compound_config = config.get('verified_urls', {}).get('compound')
    data = None

    if compound_config:
        try:
            # Attempt real fetch
            data = fetch_compound_data(compound_config)
            logger.info("Successfully fetched real compound data.")
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch real compound data: {e}. Falling back to mock data.")
            # Fallback to mock
            data = generate_mock_compound_data()
    else:
        logger.info("No verified URL for compound data found. Generating mock data.")
        data = generate_mock_compound_data()

    # Pre-check disk space (estimate: 10MB for safety)
    estimated_size = 10 * 1024 * 1024
    try:
        check_disk_space(estimated_size)
        logger.info("Disk space check passed.")
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

    # Save the data
    save_data(data, OUTPUT_COMPOUND_DATA)

    return data

def main():
    """Entry point for compound ingestion script."""
    configure_root_logger = logging.getLogger()
    configure_root_logger.setLevel(logging.INFO)
    
    try:
        data = run_compound_ingestion()
        logger.info(f"Ingestion complete. Output: {OUTPUT_COMPOUND_DATA}")
        return 0
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())