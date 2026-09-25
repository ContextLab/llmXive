"""
Zenodo API client for fetching metallic glass datasets.
Implements retry logic, rate limiting, and specific error handling.
"""
import os
import time
import logging
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# Configure logging for this module
logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when both primary and fallback DOIs are unreachable."""
    pass

class DataInsufficientError(Exception):
    """Raised when the raw dataset contains fewer than 1 row."""
    pass

def fetch_from_zenodo(doi: str, output_path: Path, max_retries: int = 5, initial_delay: float = 1.0) -> bool:
    """
    Fetch a dataset from Zenodo using a DOI.
    
    Args:
        doi: The Digital Object Identifier.
        output_path: Local path to save the CSV file.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds for exponential backoff.
        
    Returns:
        True if fetch was successful, False otherwise.
        
    Raises:
        DataUnavailableError: If the DOI is invalid or the record cannot be found (404).
        requests.RequestException: If network errors occur after retries.
    """
    base_url = "https://zenodo.org/api/records"
    endpoint = f"{base_url}/{doi}"
    
    delay = initial_delay
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempting to fetch DOI: {doi} (Attempt {attempt + 1}/{max_retries + 1})")
            
            response = requests.get(endpoint, timeout=30)
            
            if response.status_code == 200:
                record_data = response.json()
                
                # Zenodo API returns a list of files in 'files' key
                if 'files' not in record_data or not record_data['files']:
                    logger.warning(f"DOI {doi} returned no files.")
                    return False
                    
                # Assume the first file is the CSV we need, or find a .csv file
                csv_file = None
                for f in record_data['files']:
                    if f.get('key', '').endswith('.csv'):
                        csv_file = f
                        break
                
                if not csv_file:
                    # Fallback to first file if no CSV found
                    csv_file = record_data['files'][0]
                    logger.warning(f"No CSV file found in DOI {doi}, using: {csv_file.get('key')}")
                
                file_link = csv_file['links']['self']
                file_name = csv_file['key']
                
                # Download the file
                logger.info(f"Downloading file: {file_name}")
                file_response = requests.get(file_link, stream=True, timeout=300)
                file_response.raise_for_status()
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info(f"Successfully downloaded {file_name} to {output_path}")
                return True
                
            elif response.status_code == 404:
                logger.error(f"DOI {doi} not found (404).")
                raise DataUnavailableError(f"DOI {doi} returned 404 Not Found.")
                
            elif response.status_code == 429:
                logger.warning(f"Rate limit exceeded for DOI {doi}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
                continue
                
            else:
                logger.error(f"Failed to fetch DOI {doi}: Status {response.status_code}")
                if attempt == max_retries:
                    raise requests.HTTPError(f"Zenodo API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching DOI {doi}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
            continue
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error fetching DOI {doi}: {str(e)}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
            continue
        
        # If we get here, the request succeeded or failed permanently
        # If it succeeded (200), we returned True.
        # If it failed (404), we raised.
        # If it failed (other), we continue loop or raise at end.
        
    # If loop finishes without returning True or raising 404
    raise requests.RequestException(f"Failed to fetch DOI {doi} after {max_retries} retries.")

def fetch_dataset(primary_doi: str, fallback_doi: str, output_dir: Path) -> Tuple[Path, str]:
    """
    Fetch dataset attempting primary DOI first, then fallback.
    
    Args:
        primary_doi: The primary Zenodo DOI.
        fallback_doi: The fallback Zenodo DOI.
        output_dir: Directory to save the downloaded file.
        
    Returns:
        Tuple of (Path to downloaded file, DOI used)
        
    Raises:
        DataUnavailableError: If both DOIs fail.
        DataInsufficientError: If the fetched dataset has 0 rows.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try Primary
    primary_path = output_dir / f"zenodo_{primary_doi}.csv"
    try:
        success = fetch_from_zenodo(primary_doi, primary_path)
        if success:
            logger.info(f"Successfully fetched data from primary DOI: {primary_doi}")
            return primary_path, primary_doi
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI failed: {e}")
    except Exception as e:
        logger.warning(f"Primary DOI failed with unexpected error: {e}")
    
    # Try Fallback
    fallback_path = output_dir / f"zenodo_{fallback_doi}.csv"
    try:
        success = fetch_from_zenodo(fallback_doi, fallback_path)
        if success:
            logger.warning(f"Fallback DOI used successfully: {fallback_doi}")
            return fallback_path, fallback_doi
    except DataUnavailableError as e:
        logger.warning(f"Fallback DOI failed: {e}")
    except Exception as e:
        logger.warning(f"Fallback DOI failed with unexpected error: {e}")
        
    raise DataUnavailableError(f"Both primary ({primary_doi}) and fallback ({fallback_doi}) DOIs are unreachable.")

def main():
    """Main entry point for testing the client."""
    # Example usage
    primary = "10.5281/zenodo.10043838"
    fallback = "10.5281/zenodo.11023456"
    output = Path("data/raw")
    
    try:
        path, doi = fetch_dataset(primary, fallback, output)
        print(f"Data fetched from {doi} at {path}")
    except DataUnavailableError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
