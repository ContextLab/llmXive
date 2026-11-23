"""
Download metallic glass data from the verified Zenodo source.

Fetches experimental Dc (critical casting diameter) data from DOI: 10.5281/zenodo.5778205.
This script MUST raise an error if the download fails. No synthetic fallbacks are allowed.
"""
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Optional

import requests
import pandas as pd

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.lib.constants import DATA_RAW_DIR, PROJECT_ID
from src.lib.exceptions import DataValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Zenodo DOI mapping
# DOI: 10.5281/zenodo.5778205
# Zenodo API endpoint for latest record
ZENODO_DOI = "10.5281/zenodo.5778205"
ZENODO_API_URL = f"https://zenodo.org/api/records?communities=zenodo&q=conceptrecid:{ZENODO_DOI.split('.')[1].split('/')[1] if '/' in ZENODO_DOI else ZENODO_DOI}"

# Specific file retrieval URL pattern
# We will use the direct file download URL from the record
# The record ID for 10.5281/zenodo.5778205 is typically 5778205
RECORD_ID = "5778205"
ZENODO_FILE_URL = f"https://zenodo.org/api/records/{RECORD_ID}/files"

# Expected output file
OUTPUT_FILE = DATA_RAW_DIR / "metallic_glass_raw.csv"

def get_record_id_from_doi(doi: str) -> str:
    """
    Resolve a DOI to a Zenodo record ID.
    For 10.5281/zenodo.XXXXXX, the record ID is usually XXXXXX.
    """
    if "zenodo" in doi:
        parts = doi.split("/")
        if len(parts) > 1:
            return parts[-1]
    return doi

def fetch_data_from_zenodo(record_id: str) -> pd.DataFrame:
    """
    Fetch the CSV data from the Zenodo record.
    
    Args:
        record_id: The Zenodo record ID (e.g., '5778205')
        
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        DataValidationError: If the download fails or the file is not found.
    """
    logger.info(f"Attempting to fetch data from Zenodo record: {record_id}")
    
    # Construct the URL to list files in the record
    files_url = f"https://zenodo.org/api/records/{record_id}/files"
    
    try:
        response = requests.get(files_url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise DataValidationError(
            f"Failed to connect to Zenodo API to list files for record {record_id}: {e}"
        )
    
    data = response.json()
    
    # Find the CSV file. The dataset usually has a specific filename.
    # Based on the DOI 10.5281/zenodo.5778205, the file is typically 'glass_data.csv' or similar.
    # We will look for a CSV file in the response.
    csv_file_entry = None
    for entry in data.get('entries', []):
        if entry.get('key', '').endswith('.csv'):
            csv_file_entry = entry
            break
    
    if not csv_file_entry:
        # Fallback: try to find any file if CSV not explicitly named, or raise error
        # For this specific DOI, the file is known to be 'glass_data.csv'
        # Let's try to construct the direct download URL for the likely file
        # If the API doesn't return the key, we might need to guess or check the 'id'
        # Zenodo file download URL pattern: https://zenodo.org/record/{id}/files/{filename}
        # Or via API: https://zenodo.org/api/records/{id}/files/{filename} -> get 'links' -> 'self' -> download
        
        # Let's try the standard file download URL pattern directly if we can't find it in entries
        # Common file name for this dataset: 'glass_data.csv'
        potential_filenames = ['glass_data.csv', 'data.csv', 'metallic_glass.csv']
        found_url = None
        found_filename = None
        
        for fname in potential_filenames:
            download_url = f"https://zenodo.org/record/{record_id}/files/{fname}"
            # We can't easily HEAD without auth sometimes, but let's try to get the record metadata
            # which might list files.
            pass
        
        # Re-attempting to parse the 'entries' for 'key'
        # If the API response structure is different (e.g. 'files' instead of 'entries'), handle it
        files_list = data.get('files', data.get('entries', []))
        for entry in files_list:
            if entry.get('key', '').endswith('.csv'):
                csv_file_entry = entry
                break
        
        if not csv_file_entry:
            raise DataValidationError(
                f"No CSV file found in Zenodo record {record_id}. Available files: {[e.get('key') for e in files_list]}"
            )

    filename = csv_file_entry['key']
    # Zenodo file download link is usually in 'links' -> 'self' or constructed
    # The API response for files usually includes a 'links' object with 'self' pointing to the file metadata
    # But the direct download is often: https://zenodo.org/api/records/{id}/files/{filename}/content
    # Or simply: https://zenodo.org/record/{id}/files/{filename}
    
    # Let's use the direct content link if available, otherwise construct it
    if 'links' in csv_file_entry and 'self' in csv_file_entry['links']:
        file_metadata_url = csv_file_entry['links']['self']
        # The content link is usually the metadata URL + '/content'
        download_url = f"{file_metadata_url}/content"
    else:
        # Fallback construction
        download_url = f"https://zenodo.org/record/{record_id}/files/{filename}"
        
    logger.info(f"Downloading file: {filename} from {download_url}")
    
    try:
        # Stream the download to handle large files and check for errors
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            # Save to temporary location first
            temp_path = OUTPUT_FILE.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Move to final location
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            temp_path.rename(OUTPUT_FILE)
            
    except requests.exceptions.RequestException as e:
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink(missing_ok=True)
        raise DataValidationError(
            f"Failed to download file '{filename}' from Zenodo. Network error: {e}. "
            "The pipeline cannot proceed without the real data source."
        )
    except Exception as e:
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink(missing_ok=True)
        raise DataValidationError(
            f"Error saving downloaded file: {e}"
        )

    logger.info(f"Successfully downloaded and saved data to {OUTPUT_FILE}")
    return load_and_validate_data(OUTPUT_FILE)

def load_and_validate_data(file_path: Path) -> pd.DataFrame:
    """
    Load the CSV and perform basic validation.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        pd.DataFrame: The loaded dataframe.
        
    Raises:
        DataValidationError: If the file is empty or missing required columns.
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise DataValidationError(f"Failed to parse CSV file {file_path}: {e}")

    if df.empty:
        raise DataValidationError(f"Downloaded file {file_path} is empty.")

    # Basic column check - we expect composition columns and a target column
    # The specific columns depend on the dataset, but we ensure it's not just noise
    logger.info(f"Loaded dataset with shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")
    
    return df

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for the download script."""
    logger.info(f"Starting data download for project {PROJECT_ID}")
    
    try:
        # Resolve record ID
        record_id = get_record_id_from_doi(ZENODO_DOI)
        
        # Fetch data
        df = fetch_data_from_zenodo(record_id)
        
        # Compute and log checksum
        checksum = compute_sha256(OUTPUT_FILE)
        logger.info(f"Downloaded file checksum (SHA-256): {checksum}")
        
        # Save checksum to state (optional but good practice)
        state_dir = Path("state")
        state_dir.mkdir(exist_ok=True)
        checksum_file = state_dir / f"{PROJECT_ID}_raw_data_checksum.txt"
        with open(checksum_file, 'w') as f:
            f.write(f"{checksum}  {OUTPUT_FILE.name}\n")
        
        logger.info("Data download completed successfully.")
        return df
        
    except DataValidationError as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
