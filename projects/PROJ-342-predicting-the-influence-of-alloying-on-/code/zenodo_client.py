import requests
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when the dataset cannot be retrieved from Zenodo."""
    pass

class DataInsufficientError(Exception):
    """Raised when the dataset is found but contains no usable data."""
    pass

def download_csv_from_zenodo(doi: str, save_path: Path) -> bool:
    """
    Downloads the first CSV file found in a Zenodo record associated with the given DOI.
    
    Args:
        doi: The Zenodo DOI (e.g., '10.5281/zenodo.10043838').
        save_path: Path to save the downloaded CSV.
        
    Returns:
        True if successful, False otherwise.
        
    Raises:
        DataUnavailableError: If the record is not found or no CSV is available.
    """
    # Extract record ID from DOI
    try:
        record_id = doi.split('.')[-1]
    except IndexError:
        raise DataUnavailableError(f"Invalid DOI format: {doi}")

    api_url = f"https://zenodo.org/api/records/{record_id}"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Failed to fetch metadata for DOI {doi}: {e}")
        raise DataUnavailableError(f"Zenodo API unreachable or record {record_id} not found.") from e

    # Find the first CSV file in the files list
    files = data.get('files', [])
    csv_file = next((f for f in files if f.get('filename', '').endswith('.csv')), None)
    
    if not csv_file:
        logger.error(f"No CSV file found in Zenodo record {record_id}")
        raise DataUnavailableError(f"No CSV file found in Zenodo record metadata for DOI {doi}.")

    download_url = csv_file.get('links', {}).get('self')
    if not download_url:
        raise DataUnavailableError(f"Download link missing for file {csv_file.get('filename')} in record {record_id}")

    try:
        logger.info(f"Downloading CSV from {download_url}...")
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download file from {download_url}: {e}")
        raise DataUnavailableError(f"Error downloading CSV for DOI {doi}") from e
