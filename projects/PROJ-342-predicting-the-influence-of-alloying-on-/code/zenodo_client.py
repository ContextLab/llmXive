"""
Zenodo API client for fetching datasets.
"""
import os
import time
import logging
import requests
import json
from pathlib import Path
from typing import Optional

class DataUnavailableError(Exception):
    """Raised when data cannot be fetched from any source."""
    pass

class DataInsufficientError(Exception):
    """Raised when data is fetched but is insufficient (e.g., < 1 row)."""
    pass

def fetch_from_zenodo(doi: str, output_path: str, timeout: int = 300):
    """
    Fetch a dataset from Zenodo by DOI.
    
    Args:
        doi: The DOI of the dataset (e.g., '10.5281/zenodo.10043838')
        output_path: Local path to save the CSV file
        timeout: Request timeout in seconds
    
    Raises:
        DataUnavailableError: If fetch fails
    """
    logger = logging.getLogger(__name__)
    
    # Zenodo API endpoint
    api_url = f"https://zenodo.org/api/records/{doi.split('.')[-1]}"
    
    headers = {
        "Accept": "application/json"
    }
    
    # Exponential backoff retry logic
    max_retries = 5
    base_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching metadata from Zenodo API: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                data = response.json()
                # Find the file with CSV extension
                files = data.get('files', [])
                if not files:
                    # Try alternative structure
                    files = data.get('metadata', {}).get('files', [])
                
                csv_file = None
                for f in files:
                    if f.get('type') == 'other' or f.get('key', '').endswith('.csv'):
                        csv_file = f
                        break
                
                # If no specific file found, try the first one
                if not csv_file and files:
                    csv_file = files[0]
                
                if not csv_file:
                    raise DataUnavailableError(f"No files found in Zenodo record: {doi}")
                
                file_url = csv_file.get('links', {}).get('self') or csv_file.get('download_url')
                if not file_url:
                    # Construct download URL
                    record_id = data.get('id')
                    file_name = csv_file.get('key', 'data.csv')
                    file_url = f"https://zenodo.org/api/records/{record_id}/files/{file_name}/content"
                
                logger.info(f"Downloading file from: {file_url}")
                file_response = requests.get(file_url, timeout=timeout)
                file_response.raise_for_status()
                
                # Save to file
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path_obj, 'wb') as f:
                    f.write(file_response.content)
                
                logger.info(f"Successfully downloaded file to: {output_path}")
                return
            
            elif response.status_code == 404:
                raise DataUnavailableError(f"DOI not found: {doi} (404)")
            else:
                logger.warning(f"Zenodo API returned status {response.status_code}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise DataUnavailableError(f"Failed to fetch from Zenodo after {max_retries} attempts: {str(e)}")
    
    raise DataUnavailableError(f"Failed to fetch from Zenodo: {doi}")

def fetch_dataset(doi: str, output_dir: str) -> Path:
    """
    Fetch dataset and return the path to the downloaded file.
    
    Args:
        doi: DOI of the dataset
        output_dir: Directory to save the file
    
    Returns:
        Path to the downloaded file
    """
    output_path = Path(output_dir) / f"zenodo_{doi.split('.')[-1]}.csv"
    fetch_from_zenodo(doi, str(output_path))
    return output_path

def main():
    """CLI entry point for testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Fetch dataset from Zenodo")
    parser.add_argument("--doi", required=True, help="DOI to fetch")
    parser.add_argument("--output", required=True, help="Output file path")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    try:
        fetch_from_zenodo(args.doi, args.output)
        print(f"Successfully fetched {args.doi} to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
