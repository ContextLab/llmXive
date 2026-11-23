"""
Zenodo client for downloading datasets by DOI.

Provides functions to download CSV files from Zenodo records and handle
various failure modes gracefully.
"""
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when data cannot be retrieved from the specified source."""
    pass

class DataInsufficientError(Exception):
    """Raised when insufficient valid data remains after processing."""
    pass

def download_csv_from_zenodo(doi: str, output_path: Path) -> None:
    """
    Download a CSV file from a Zenodo record by DOI.
    
    Args:
        doi: The DOI identifier (e.g., '10.5281/zenodo.10043838')
        output_path: Path where the CSV file will be saved
    
    Raises:
        DataUnavailableError: If the DOI is invalid or no CSV file is found
    """
    # Convert DOI to Zenodo record ID
    # DOI format: 10.5281/zenodo.XXXXXX
    try:
        record_id = doi.split('.')[-1]
    except (IndexError, AttributeError):
        raise DataUnavailableError(f"Invalid DOI format: {doi}")
    
    # Zenodo API endpoint
    zenodo_api = f"https://zenodo.org/api/records/{record_id}"
    
    try:
        # Fetch record metadata
        response = requests.get(zenodo_api, timeout=30)
        response.raise_for_status()
        record = response.json()
    except requests.RequestException as e:
        raise DataUnavailableError(f"Failed to fetch record {record_id}: {e}")
    
    # Find CSV file in the record
    csv_file = None
    if 'files' in record:
        for file_info in record['files']:
            if file_info['key'].endswith('.csv'):
                csv_file = file_info
                break
    
    if csv_file is None:
        raise DataUnavailableError(f"No CSV file found in Zenodo record {doi}")
    
    # Download the CSV file
    try:
        file_url = csv_file['links']['self']
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()
        
        # Write to output path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Downloaded {csv_file['key']} from {doi} to {output_path}")
    except requests.RequestException as e:
        raise DataUnavailableError(f"Failed to download CSV from {doi}: {e}")

def fetch_from_zenodo(doi: str):
    """
    Fetch data from Zenodo by DOI and return as a pandas DataFrame.
    
    Args:
        doi: The DOI identifier
    
    Returns:
        pandas.DataFrame: The loaded CSV data
    
    Raises:
        DataUnavailableError: If the data cannot be retrieved
    """
    import pandas as pd
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        download_csv_from_zenodo(doi, tmp_path)
        df = pd.read_csv(tmp_path)
        
        # Normalize column names
        if 'tg_value' in df.columns and 'Tg' not in df.columns:
            df = df.rename(columns={'tg_value': 'Tg'})
        
        return df
    finally:
        tmp_path.unlink(missing_ok=True)