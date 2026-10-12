import requests
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when the dataset cannot be retrieved from Zenodo."""
    pass

class DataInsufficientError(Exception):
    """Raised when the retrieved dataset contains no usable records."""
    pass

def download_csv_from_zenodo(doi: str, output_path: Path) -> None:
    """
    Downloads a CSV file from Zenodo given a DOI.
    
    Args:
        doi: The Zenodo DOI (e.g., '10.5281/zenodo.10043838').
        output_path: Path to save the downloaded CSV.
    
    Raises:
        DataUnavailableError: If the record or CSV file is not found.
    """
    # Extract record ID from DOI (e.g., 10.5281/zenodo.10043838 -> 10043838)
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
        logger.error(f"Failed to fetch Zenodo metadata for DOI {doi}: {e}")
        raise DataUnavailableError(f"Zenodo API error for DOI {doi}: {e}") from e

    # Find the CSV file in the record's files list
    files = data.get('files', [])
    csv_file = next((f for f in files if f.get('key', '').endswith('.csv') or f.get('filename', '').endswith('.csv')), None)
    
    if not csv_file:
        logger.error(f"No CSV file found in Zenodo record {doi}")
        raise DataUnavailableError(f"No CSV file found in Zenodo record {doi}")

    download_url = csv_file.get('links', {}).get('download')
    if not download_url:
        logger.error(f"No download link found for CSV in Zenodo record {doi}")
        raise DataUnavailableError(f"No download link found for CSV in Zenodo record {doi}")

    try:
        logger.info(f"Downloading CSV from {download_url}...")
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Successfully downloaded CSV to {output_path}")
    except Exception as e:
        logger.error(f"Failed to download file from {download_url}: {e}")
        raise DataUnavailableError(f"Download failed for DOI {doi}: {e}") from e
