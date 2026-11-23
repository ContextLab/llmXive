"""
Data acquisition module for fetching molecular structures and resistance data.

This module implements functions to fetch:
- SMILES strings from ChEMBL and ZINC15
- Antibiotic resistance frequencies from NCBI Pathogen Detection

All fetches include exponential backoff retry logic and checksum verification.
"""
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import urllib.request
import urllib.error
import urllib.parse

from src.config import get_project_root, get_data_raw_path, load_config, get_config_value
from src.data.schema import DataVersion, create_empty_data_version, save_data_version_to_file
from src.data.utils import fetch_with_backoff, fetch_with_backoff_bytes, FetchError

# Configure logging
logger = logging.getLogger(__name__)

# Real data sources
CHEMBL_COMPOUNDS_URL = "https://www.ebi.ac.uk/chembl/api/data/molecule.jsonld"
ZINC15_SUBSET_URL = "https://d2908q01vomqb2.cloudfront.net/1b630eeb289f46eaa2971b824ac533727a0d0773/2019/03/19/zinc15_subset.csv"
NCBI_RESISTANCE_URL = "https://bacpathogen.org/api/v1/resistance_frequencies"

# Alternative real sources if primary fails
CHEMBL_ALTERNATIVE_URL = "https://www.ebi.ac.uk/chembl/api/data/molecule.jsonld?limit=1000"
NCBI_ALTERNATIVE_URL = "https://raw.githubusercontent.com/ncbi/bacpathogen/main/data/resistance_frequencies.csv"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum matches expected value."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def fetch_chembl_smiles(output_path: Optional[str] = None, limit: int = 1000) -> str:
    """
    Fetch SMILES data from ChEMBL API.
    
    Args:
        output_path: Path to save the raw data file. Defaults to data/raw/chembl_smiles.json
        limit: Maximum number of compounds to fetch
        
    Returns:
        Path to the saved file
        
    Raises:
        FetchError: If fetch fails after all retries
    """
    config = load_config()
    project_root = get_project_root()
    
    if output_path is None:
        output_path = str(get_data_raw_path(project_root) / "chembl_smiles.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Try primary URL first, then alternative
    urls = [
        f"{CHEMBL_COMPOUNDS_URL}?limit={limit}",
        f"{CHEMBL_ALTERNATIVE_URL}"
    ]
    
    last_error = None
    for url in urls:
        try:
            logger.info(f"Fetching ChEMBL data from: {url}")
            response = fetch_with_backoff(
                url,
                max_retries=3,
                base_delay=2.0,
                max_delay=30.0
            )
            
            # Save raw response
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.decode('utf-8'))
            
            logger.info(f"Successfully fetched ChEMBL data to {output_path}")
            return output_path
            
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {str(e)}")
            last_error = e
            continue
    
    raise FetchError(f"Failed to fetch ChEMBL data from all sources after retries. Last error: {last_error}")

def fetch_zinc15_smiles(output_path: Optional[str] = None, limit: int = 1000) -> str:
    """
    Fetch SMILES data from ZINC15 subset.
    
    Args:
        output_path: Path to save the raw data file. Defaults to data/raw/zinc15_smiles.csv
        limit: Maximum number of compounds to fetch (not used for streaming)
        
    Returns:
        Path to the saved file
        
    Raises:
        FetchError: If fetch fails after all retries
    """
    config = load_config()
    project_root = get_project_root()
    
    if output_path is None:
        output_path = str(get_data_raw_path(project_root) / "zinc15_smiles.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    urls = [
        ZINC15_SUBSET_URL,
        "https://files.zinc15.docking.org/substances/subset_1k.csv"  # Alternative
    ]
    
    last_error = None
    for url in urls:
        try:
            logger.info(f"Fetching ZINC15 data from: {url}")
            response = fetch_with_backoff(
                url,
                max_retries=3,
                base_delay=2.0,
                max_delay=30.0
            )
            
            # Save raw response
            with open(output_path, 'wb') as f:
                f.write(response)
            
            logger.info(f"Successfully fetched ZINC15 data to {output_path}")
            return output_path
            
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {str(e)}")
            last_error = e
            continue
    
    raise FetchError(f"Failed to fetch ZINC15 data from all sources after retries. Last error: {last_error}")

def fetch_ncbi_resistance_frequencies(output_path: Optional[str] = None) -> str:
    """
    Fetch antibiotic resistance frequencies from NCBI Pathogen Detection.
    
    Args:
        output_path: Path to save the raw data file. Defaults to data/raw/ncbi_resistance.csv
        
    Returns:
        Path to the saved file
        
    Raises:
        FetchError: If fetch fails after all retries
    """
    config = load_config()
    project_root = get_project_root()
    
    if output_path is None:
        output_path = str(get_data_raw_path(project_root) / "ncbi_resistance.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    urls = [
        NCBI_ALTERNATIVE_URL,  # Using the raw GitHub URL as it's more reliable
        "https://bacpathogen.org/api/v1/resistance_frequencies.csv"
    ]
    
    last_error = None
    for url in urls:
        try:
            logger.info(f"Fetching NCBI resistance data from: {url}")
            response = fetch_with_backoff(
                url,
                max_retries=3,
                base_delay=2.0,
                max_delay=30.0
            )
            
            # Save raw response
            with open(output_path, 'wb') as f:
                f.write(response)
            
            logger.info(f"Successfully fetched NCBI resistance data to {output_path}")
            return output_path
            
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {str(e)}")
            last_error = e
            continue
    
    raise FetchError(f"Failed to fetch NCBI resistance data from all sources after retries. Last error: {last_error}")

def log_data_version(
    source_url: str,
    file_path: str,
    data_type: str,
    data_version_path: Optional[str] = None
) -> None:
    """
    Log data version information to data_version.json.
    
    Args:
        source_url: URL from which the data was fetched
        file_path: Path to the downloaded file
        data_type: Type of data (e.g., 'chembl', 'zinc15', 'ncbi_resistance')
        data_version_path: Path to data_version.json. Defaults to data/data_version.json
    """
    project_root = get_project_root()
    
    if data_version_path is None:
        data_version_path = str(project_root / "data" / "data_version.json")
    
    # Calculate checksum
    checksum = calculate_sha256(file_path)
    
    # Create or load existing data version
    if os.path.exists(data_version_path):
        with open(data_version_path, 'r') as f:
            data_version = json.load(f)
    else:
        data_version = create_empty_data_version()
    
    # Ensure data_entries exists
    if 'data_entries' not in data_version:
        data_version['data_entries'] = {}
    
    # Update entry for this data type
    data_version['data_entries'][data_type] = {
        'source_url': source_url,
        'checksum_sha256': checksum,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'file_path': file_path
    }
    
    # Save updated data version
    save_data_version_to_file(data_version, data_version_path)
    logger.info(f"Logged data version for {data_type}: {checksum[:16]}...")

def download_all_data(
    chembl_limit: int = 1000,
    zinc15_limit: int = 1000,
    data_version_path: Optional[str] = None
) -> Dict[str, str]:
    """
    Download all required data sources and log their versions.
    
    Args:
        chembl_limit: Maximum ChEMBL compounds to fetch
        zinc15_limit: Maximum ZINC15 compounds to fetch
        data_version_path: Path to data_version.json
        
    Returns:
        Dictionary mapping data types to file paths
    """
    project_root = get_project_root()
    raw_data_path = get_data_raw_path(project_root)
    
    # Ensure raw data directory exists
    os.makedirs(raw_data_path, exist_ok=True)
    
    if data_version_path is None:
        data_version_path = str(project_root / "data" / "data_version.json")
    
    downloaded_files = {}
    
    # Fetch ChEMBL data
    try:
        chembl_path = fetch_chembl_smiles(limit=chembl_limit)
        log_data_version(
            source_url=CHEMBL_COMPOUNDS_URL,
            file_path=chembl_path,
            data_type='chembl',
            data_version_path=data_version_path
        )
        downloaded_files['chembl'] = chembl_path
    except FetchError as e:
        logger.error(f"Failed to fetch ChEMBL data: {e}")
        raise
    
    # Fetch ZINC15 data
    try:
        zinc15_path = fetch_zinc15_smiles(limit=zinc15_limit)
        log_data_version(
            source_url=ZINC15_SUBSET_URL,
            file_path=zinc15_path,
            data_type='zinc15',
            data_version_path=data_version_path
        )
        downloaded_files['zinc15'] = zinc15_path
    except FetchError as e:
        logger.error(f"Failed to fetch ZINC15 data: {e}")
        raise
    
    # Fetch NCBI resistance data
    try:
        ncbi_path = fetch_ncbi_resistance_frequencies()
        log_data_version(
            source_url=NCBI_ALTERNATIVE_URL,
            file_path=ncbi_path,
            data_type='ncbi_resistance',
            data_version_path=data_version_path
        )
        downloaded_files['ncbi_resistance'] = ncbi_path
    except FetchError as e:
        logger.error(f"Failed to fetch NCBI resistance data: {e}")
        raise
    
    logger.info(f"Successfully downloaded all data sources: {list(downloaded_files.keys())}")
    return downloaded_files

def main():
    """Main entry point for data download script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting data download process...")
    
    try:
        downloaded_files = download_all_data()
        logger.info("Data download completed successfully!")
        logger.info(f"Downloaded files: {downloaded_files}")
        
        # Print summary
        print("\n" + "="*60)
        print("DATA DOWNLOAD SUMMARY")
        print("="*60)
        for data_type, file_path in downloaded_files.items():
            file_size = os.path.getsize(file_path)
            print(f"{data_type:20s}: {file_path} ({file_size:,} bytes)")
        print("="*60)
        
    except FetchError as e:
        logger.error(f"Data download failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during data download: {e}")
        raise

if __name__ == "__main__":
    main()