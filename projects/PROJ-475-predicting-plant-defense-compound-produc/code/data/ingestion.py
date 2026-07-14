"""
Data Ingestion Module.
Fetches or generates mock data for Genomic, Environmental, and Compound sources.
"""
import json
import os
import sys
import requests
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logging import get_module_logger, configure_root_logger
from utils.io import check_disk_space, DiskSpaceError
from data.mock_generator import generate_all_mock_data
from config import get_config

logger = get_module_logger(__name__)

RAW_DIR = Path("data/raw")

# Output paths
GENOMIC_OUTPUT_PATH = RAW_DIR / "genomic_vcf.json"
ENV_OUTPUT_PATH = RAW_DIR / "env_data.json"
COMPOUND_OUTPUT_PATH = RAW_DIR / "compound_data.json"

# Verified URLs (Placeholder for real URLs as per spec)
VERIFIED_URLS = {
    'genomic': 'https://api.example.com/genomic_data', # Replace with real NCBI SRA endpoint if available
    'env': 'https://api.example.com/env_data',         # Replace with real WorldClim/GBIF endpoint
    'compound': 'https://api.example.com/compound_data' # Replace with real ChemBank/PhenolExplorer endpoint
}

def save_data(data: List[Dict], output_path: Path) -> None:
    """Saves data to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved data to {output_path}")

def fetch_genomic_data() -> List[Dict]:
    """Fetches genomic data from verified URL or generates mock data."""
    config = get_config()
    url = VERIFIED_URLS['genomic']
    
    # Check if verified URL is configured (simulated by checking config)
    # In real scenario, this would check config.verified_urls['genomic']
    use_mock = not config.get('verified_urls', {}).get('genomic', False)
    
    if not use_mock:
        try:
            logger.info(f"Fetching genomic data from {url}...")
            # Simulate fetch (replace with real requests.get(url).json())
            # Since real URL is placeholder, we fallback to mock for this demo to avoid network failure
            # In a real implementation with a real URL, this would work.
            # For now, we treat the placeholder as "not verified" to ensure run-ability.
            raise ValueError("Placeholder URL detected, falling back to mock.")
        except Exception as e:
            logger.warning(f"Fetch failed ({e}). Falling back to mock data generation for genomic data.")
            use_mock = True
    
    if use_mock:
        logger.info("Generating mock genomic data.")
        data = generate_all_mock_data()['genomic']
    
    # Post-check disk usage
    try:
        check_disk_space(sys.getsizeof(data))
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise
    
    save_data(data, GENOMIC_OUTPUT_PATH)
    return data

def fetch_environmental_data() -> List[Dict]:
    """Fetches environmental data from verified URL or generates mock data."""
    config = get_config()
    url = VERIFIED_URLS['env']
    use_mock = not config.get('verified_urls', {}).get('env', False)
    
    if not use_mock:
        try:
            logger.info(f"Fetching environmental data from {url}...")
            raise ValueError("Placeholder URL detected, falling back to mock.")
        except Exception as e:
            logger.warning(f"Fetch failed ({e}). Falling back to mock data generation for environmental data.")
            use_mock = True
    
    if use_mock:
        logger.info("Generating mock environmental data.")
        data = generate_all_mock_data()['environmental']
    
    try:
        check_disk_space(sys.getsizeof(data))
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise
    
    save_data(data, ENV_OUTPUT_PATH)
    return data

def fetch_compound_data() -> List[Dict]:
    """Fetches compound profiles from verified URL or generates mock data."""
    config = get_config()
    url = VERIFIED_URLS['compound']
    use_mock = not config.get('verified_urls', {}).get('compound', False)
    
    if not use_mock:
        try:
            logger.info(f"Fetching compound data from {url}...")
            raise ValueError("Placeholder URL detected, falling back to mock.")
        except Exception as e:
            logger.warning(f"Fetch failed ({e}). Falling back to mock data generation for compound profiles.")
            use_mock = True
    
    if use_mock:
        logger.info("Generating mock compound data.")
        data = generate_all_mock_data()['compound']
    
    try:
        check_disk_space(sys.getsizeof(data))
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise
    
    save_data(data, COMPOUND_OUTPUT_PATH)
    return data

def run_all_ingestion() -> Dict[str, List[Dict]]:
    """Runs all ingestion steps."""
    logger.info("Starting ingestion pipeline.")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    genomic = fetch_genomic_data()
    env_data = fetch_environmental_data()
    compound = fetch_compound_data()
    
    return {
        'genomic': genomic,
        'environmental': env_data,
        'compound': compound
    }

def main():
    """Entry point for ingestion script."""
    configure_root_logger()
    run_all_ingestion()

if __name__ == "__main__":
    main()
