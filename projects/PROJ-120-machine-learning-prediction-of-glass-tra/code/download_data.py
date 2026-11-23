"""
Data Acquisition Module for Glass Transition Temperature Prediction.

This module implements the fetcher for raw glass composition data from the
NIST Materials Data Repository via Zenodo. It strictly adheres to the
'Fail Loudly' constraint: if the real data cannot be fetched, it raises
a DataFetchError rather than falling back to synthetic data.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

import requests

# Project imports
from config import get_zenodo_doi, get_zenodo_api_url, get_raw_data_dir
from utils import setup_logging, ensure_directory
from exceptions import DataFetchError

# Configure logging
logger = setup_logging(__name__)

# Zenodo configuration
ZENODO_BASE_URL = "https://zenodo.org/api"
# The specific DOI for the glass transition dataset (NIST/ICDD glass data)
# Using a known stable record for glass Tg data: 10.1103/PhysRevB.88.094201 (example)
# Or a generic Zenodo record for glass data. We will resolve the DOI dynamically.
# Common dataset: "Glass Transition Temperature Dataset"
# For this implementation, we assume the DOI is configured in .env via get_zenodo_doi()
# If not, we default to a known public record if the env is missing, but strictly
# we prefer the env var to ensure the user intends to fetch that specific dataset.

def fetch_raw_glass_data(output_dir: Optional[Path] = None) -> Path:
    """
    Fetches the raw glass composition CSV from Zenodo using the configured DOI.

    This function:
    1. Resolves the Zenodo DOI from configuration.
    2. Determines the latest file version URL.
    3. Downloads the file to the raw data directory.
    4. Validates the download (checks for non-zero size).

    Args:
        output_dir: Optional directory path. Defaults to config.get_raw_data_dir().

    Raises:
        DataFetchError: If the DOI is missing, the fetch fails, or the file is empty.
    """
    if output_dir is None:
        output_dir = get_raw_data_dir()

    ensure_directory(output_dir)

    doi = get_zenodo_doi()
    if not doi:
        raise DataFetchError(
            "Zenodo DOI not configured. "
            "Please set ZENODO_DOI in the .env file or update config.py."
        )

    # Construct the Zenodo API URL for the specific DOI
    # Zenodo API endpoint for a specific record: /api/records/{record_id}
    # DOI format: 10.5281/zenodo.XXXXX
    # We need to extract the record ID or use the DOI directly in the query.
    # Zenodo supports searching by DOI: /api/records/?q=doi:"10.5281/zenodo.XXX"
    
    logger.info(f"Attempting to fetch data for DOI: {doi}")
    
    # Zenodo search API to find the record by DOI
    search_url = f"{ZENODO_BASE_URL}/records"
    params = {"q": f"doi:{doi}", "sort": "version", "order": "desc", "size": 1}
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("hits") or not data["hits"]["hits"]:
            raise DataFetchError(
                f"No records found for DOI: {doi}. "
                "Verify the DOI is correct and the record is public."
            )
        
        record = data["hits"]["hits"][0]
        record_id = record["id"]
        # Get the latest version ID if multiple versions exist
        latest_record_id = record["latest_id"] or record_id
        
        logger.info(f"Found record ID: {latest_record_id}")
        
        # Fetch the specific record details to get the file download URL
        record_url = f"{ZENODO_BASE_URL}/records/{latest_record_id}"
        record_response = requests.get(record_url, timeout=30)
        record_response.raise_for_status()
        record_data = record_response.json()
        
        # Locate the data file (usually a CSV)
        files = record_data.get("files", [])
        if not files:
            # Try 'latest' files if 'files' is empty in this endpoint version
            # Zenodo API v1 vs v2 differences. 
            # In v1, files are in 'files'. In v2, they are in 'files' under 'versions' or directly.
            # Fallback: look for 'latest_files' or similar if standard 'files' is missing.
            # However, standard Zenodo API v1 returns 'files' in the record.
            # Let's check the 'metadata' for file info if needed, but usually 'files' is present.
            # If the record is a 'concept' DOI, we need the version.
            # The search above returned the latest version usually.
            pass

        if not files:
            # Fallback for Zenodo API variations: check 'versions'
             versions = record_data.get("versions", [])
             if versions:
                 # Get the latest version details
                 latest_ver = versions[-1] # Usually sorted
                 ver_id = latest_ver.get("id")
                 if ver_id:
                     ver_response = requests.get(f"{ZENODO_BASE_URL}/records/{ver_id}", timeout=30)
                     ver_response.raise_for_status()
                     files = ver_response.json().get("files", [])

        if not files:
            raise DataFetchError(
                f"Record {latest_record_id} contains no downloadable files."
            )

        # Find the CSV file
        target_file = None
        for f in files:
            if f.get("key", "").lower().endswith(".csv"):
                target_file = f
                break
        
        if not target_file:
            # If no CSV, take the first file (assuming it's the data)
            target_file = files[0]
            logger.warning("No CSV file found. Downloading the first available file.")

        file_key = target_file["key"]
        download_url = target_file["download_url"]
        expected_filename = file_key

        output_path = output_dir / expected_filename
        
        logger.info(f"Downloading {download_url} to {output_path}")
        
        # Stream download to handle large files
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
        
        # Validation
        if output_path.stat().st_size == 0:
            raise DataFetchError(
                f"Downloaded file {output_path} is empty. "
                "The data source might be corrupted or the link invalid."
            )
        
        logger.info(f"Successfully downloaded {output_path} ({output_path.stat().st_size} bytes)")
        return output_path

    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Failed to fetch data from Zenodo: {e}") from e
    except ValueError as e:
        raise DataFetchError(f"Invalid response from Zenodo API: {e}") from e
    except Exception as e:
        raise DataFetchError(f"Unexpected error during data fetch: {e}") from e

def main():
    """Entry point for the data download script."""
    logger.info("Starting data acquisition for Glass Transition Temperature project.")
    try:
        output_path = fetch_raw_glass_data()
        logger.info(f"Data acquisition complete. File saved at: {output_path}")
        return 0
    except DataFetchError as e:
        logger.error(f"Data acquisition failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unhandled exception in data acquisition: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())