"""
Data ingestion script for fetching alloy data from Zenodo (Science Advances).

Fetches data from DOI: 10.1126/sciadv.aaq1566.
Falls back to synthetic data generation if the primary source is unavailable.
"""
import os
import sys
import logging
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_zenodo_doi, get_raw_data_path, ensure_data_directories, get_env_path
from utils.synthetic import generate_synthetic_dataset, save_synthetic_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zenodo API endpoint for record files
ZENOODO_API_BASE = "https://zenodo.org/api"

def get_zenodo_record_id(doi: str) -> Optional[str]:
    """
    Resolve a DOI to a Zenodo record ID.
    
    Args:
        doi: The DOI string (e.g., '10.1126/sciadv.aaq1566')
        
    Returns:
        The Zenodo record ID as a string, or None if resolution fails.
    """
    try:
        url = f"https://doi.org/{doi}"
        # Follow redirects to get the actual Zenodo URL
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code == 200:
            final_url = response.url
            # Extract record ID from URL like https://zenodo.org/record/123456
            if "zenodo.org/record/" in final_url:
                record_id = final_url.split("zenodo.org/record/")[-1].split("/")[0]
                logger.info(f"Resolved DOI {doi} to Zenodo record ID: {record_id}")
                return record_id
        logger.warning(f"Failed to resolve DOI {doi} to Zenodo record. Status: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error resolving DOI {doi}: {e}")
        return None

def get_zenodo_files(record_id: str) -> List[Dict[str, Any]]:
    """
    Fetch list of files for a given Zenodo record ID.
    
    Args:
        record_id: Zenodo record ID
        
    Returns:
        List of file metadata dictionaries.
    """
    try:
        url = f"{ZENOODO_API_BASE}/records/{record_id}/files"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        files = data.get('hits', {}).get('hits', [])
        logger.info(f"Found {len(files)} files in Zenodo record {record_id}")
        return files
    except Exception as e:
        logger.error(f"Error fetching files for record {record_id}: {e}")
        return []

def download_file(file_metadata: Dict[str, Any], output_path: Path) -> bool:
    """
    Download a file from Zenodo to the specified output path.
    
    Args:
        file_metadata: Metadata dictionary containing 'links' -> 'self'
        output_path: Local path to save the file
        
    Returns:
        True if download successful, False otherwise.
    """
    try:
        download_url = file_metadata['links']['self']
        filename = file_metadata.get('key', 'unknown_file')
        logger.info(f"Downloading {filename} from {download_url}")
        
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded {filename} to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading file {file_metadata.get('key', 'unknown')}: {e}")
        return False

def fetch_zenodo_data(doi: str = None, target_filename: str = "alloy_data.csv") -> Optional[pd.DataFrame]:
    """
    Main function to fetch data from Zenodo.
    
    Args:
        doi: DOI to fetch (defaults to config)
        target_filename: Expected filename in the Zenodo record
        
    Returns:
        DataFrame with the fetched data, or None if fetch fails.
    """
    if doi is None:
        doi = get_zenodo_doi()
    
    logger.info(f"Attempting to fetch data from Zenodo DOI: {doi}")
    
    # Step 1: Resolve DOI to Record ID
    record_id = get_zenodo_record_id(doi)
    if not record_id:
        logger.error(f"Could not resolve DOI {doi} to a Zenodo record.")
        return None
    
    # Step 2: Get file list
    files = get_zenodo_files(record_id)
    if not files:
        logger.error(f"No files found in Zenodo record {record_id}.")
        return None
    
    # Step 3: Find the target file
    target_file = None
    for f in files:
        if f.get('key') == target_filename or f.get('filename') == target_filename:
            target_file = f
            break
    
    if not target_file:
        logger.warning(f"Target file '{target_filename}' not found in record {record_id}. "
                       f"Available files: {[f.get('key') for f in files]}")
        # If exact match fails, try to find a CSV file as a fallback
        csv_files = [f for f in files if f.get('key', '').endswith('.csv')]
        if csv_files:
            logger.info(f"Using first available CSV file: {csv_files[0].get('key')}")
            target_file = csv_files[0]
        else:
            logger.error("No CSV files found in the record.")
            return None
    
    # Step 4: Download the file
    output_path = get_raw_data_path() / target_filename
    if not download_file(target_file, output_path):
        logger.error("Failed to download the file from Zenodo.")
        return None
    
    # Step 5: Load into DataFrame
    try:
        df = pd.read_csv(output_path)
        logger.info(f"Successfully loaded {len(df)} rows from {target_filename}")
        return df
    except Exception as e:
        logger.error(f"Error reading CSV file {output_path}: {e}")
        return None

def generate_fallback_data(target_rows: int = 1500) -> pd.DataFrame:
    """
    Generate synthetic data as a fallback when Zenodo is unavailable.
    
    Args:
        target_rows: Number of rows to generate
        
    Returns:
        DataFrame with synthetic data.
    """
    logger.info(f"Generating {target_rows} rows of synthetic fallback data.")
    try:
        df = generate_synthetic_dataset(n_samples=target_rows)
        logger.info(f"Successfully generated synthetic dataset with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to generate synthetic fallback data: {e}")
        raise

def main():
    """
    Main entry point for the Zenodo ingestion script.
    
    Logic:
    1. Attempt to fetch real data from Zenodo.
    2. If fetch fails (network, 404, timeout, etc.), trigger synthetic generation.
    3. Save the resulting DataFrame to data/raw/alloy_data.csv.
    """
    ensure_data_directories()
    raw_data_path = get_raw_data_path()
    output_file = raw_data_path / "alloy_data.csv"
    
    df = None
    source = "unknown"
    
    # Attempt real fetch
    try:
        df = fetch_zenodo_data()
        if df is not None:
            source = "Zenodo (Science Advances)"
            logger.info("Real data fetched successfully from Zenodo.")
        else:
            logger.warning("Real data fetch returned None (file not found or parse error).")
    except Exception as e:
        logger.error(f"Exception during Zenodo fetch: {e}")
    
    # Fallback to synthetic if real fetch failed
    if df is None:
        logger.info("Triggering synthetic data generation as fallback.")
        try:
            df = generate_fallback_data(target_rows=1500)
            source = "Synthetic Fallback"
            logger.info("Synthetic data generated successfully.")
        except Exception as e:
            logger.critical(f"Failed to generate synthetic fallback data: {e}")
            # Re-raise to indicate pipeline failure if both sources fail
            raise RuntimeError("Both Zenodo fetch and synthetic fallback generation failed.")
    
    # Save the result
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        logger.info(f"Saved dataset to {output_file} ({len(df)} rows).")
        
        # Log a summary
        logger.info(f"Dataset columns: {list(df.columns)}")
        if 'phase' in df.columns:
            logger.info(f"Phase distribution:\n{df['phase'].value_counts()}")
        
    except Exception as e:
        logger.error(f"Failed to save dataset to {output_file}: {e}")
        raise

if __name__ == "__main__":
    main()