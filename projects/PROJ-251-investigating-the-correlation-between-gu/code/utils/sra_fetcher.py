import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import requests
import pandas as pd
import json

from utils.logging_config import get_logger
from utils.config import get_ncbi_api_key

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when data cannot be fetched from the real source."""
    pass

def _fetch_study_metadata(accession: str) -> dict:
    """Fetch study metadata from NCBI E-utilities."""
    api_key = get_ncbi_api_key()
    key_param = f"&api_key={api_key}" if api_key else ""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    
    params = {
        "db": "sra",
        "id": accession,
        "retmode": "json"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "result" not in data or accession not in data["result"]:
            raise DataUnavailableError(f"NCBI API returned no result for {accession}")
        
        return data["result"][accession]
    except requests.exceptions.RequestException as e:
        raise DataUnavailableError(f"Network error fetching metadata: {str(e)}")
    except json.JSONDecodeError:
        raise DataUnavailableError("Invalid JSON response from NCBI API")

def _construct_download_url(accession: str) -> Optional[str]:
    """
    Construct a URL to fetch pre-processed data.
    Since NCBI SRA primarily stores raw reads (fastq), we attempt to find
    a linked BioProject or a specific data repository URL if available in metadata.
    
    For this implementation, we assume the study provides a direct link to 
    processed data in the 'StudyDescription' or 'BioProject' field, 
    or we attempt to fetch from a standard repository structure if the 
    study ID is known to host processed files (e.g., ENA or a specific lab repo).
    
    NOTE: In a real-world scenario, this often requires parsing the 
    'StudyDescription' for a URL or querying the associated BioProject.
    """
    metadata = _fetch_study_metadata(accession)
    description = metadata.get("StudyDescription", "")
    
    # Heuristic: Look for a URL in the description
    # This is a simplified heuristic. Real implementations might parse XML or 
    # query the BioProject API for data repositories.
    import re
    urls = re.findall(r'https?://[^\s]+', description)
    
    # Filter for likely data repositories (ENA, SRA processed, GitHub, Zenodo)
    valid_urls = [u for u in urls if any(domain in u for domain in ['ena', 'sra', 'github', 'zenodo', 'figshare'])]
    
    if valid_urls:
        logger.info(f"Found potential data URL in metadata: {valid_urls[0]}")
        return valid_urls[0]
    
    # Fallback: Try to construct a URL for a common repository structure
    # e.g., if the study is hosted on ENA directly with processed files
    # This is speculative and might fail if the specific study doesn't follow it.
    ena_base = "https://www.ebi.ac.uk/ena/browser/api/xml/"
    # We cannot easily guess the processed file path without more metadata.
    # For the purpose of this task, we rely on the metadata extraction.
    # If no URL is found in metadata, we raise an error to fail loudly.
    logger.warning("No direct data URL found in study metadata.")
    return None

def fetch_otu_table(accession: str) -> Optional[pd.DataFrame]:
    """
    Fetch pre-processed OTU table for the given SRA accession.
    Attempts to locate a CSV or TSV file linked in the study metadata.
    """
    url = _construct_download_url(accession)
    
    if not url:
        # If we can't find a URL, we cannot fetch the OTU table.
        # We fail loudly as per constraints.
        raise DataUnavailableError(f"Could not locate pre-processed OTU table URL for accession {accession}")
    
    try:
        logger.info(f"Attempting to download OTU table from: {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Try to parse as CSV
        # The content might be a zip, but we assume direct CSV/TSV for this pipeline
        # If it's text/csv or text/plain, we parse it.
        if 'text' in response.headers.get('Content-Type', ''):
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            # Validate required columns
            required_cols = ['subject_id'] # At least an ID column
            if not any(col in df.columns for col in required_cols):
                raise DataUnavailableError("Fetched file does not contain expected 'subject_id' column.")
            return df
        else:
            # If it's binary or zip, we can't process it directly here without extraction
            # This implies the URL points to a zip file.
            raise DataUnavailableError("The provided URL does not point to a direct CSV/TSV file. "
                                       "Extraction logic not implemented in this fetcher.")
    except requests.exceptions.RequestException as e:
        raise DataUnavailableError(f"Failed to download OTU table from {url}: {str(e)}")
    except pd.errors.EmptyDataError:
        raise DataUnavailableError("The downloaded file is empty.")

def fetch_serology_metadata(accession: str) -> Optional[pd.DataFrame]:
    """
    Fetch serology metadata for the given SRA accession.
    Similar logic to OTU table, looking for a linked metadata file.
    """
    url = _construct_download_url(accession)
    
    if not url:
        raise DataUnavailableError(f"Could not locate serology metadata URL for accession {accession}")
    
    try:
        logger.info(f"Attempting to download serology metadata from: {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        if 'text' in response.headers.get('Content-Type', ''):
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            # Validate required columns
            required_cols = ['subject_id']
            if not any(col in df.columns for col in required_cols):
                raise DataUnavailableError("Fetched file does not contain expected 'subject_id' column.")
            return df
        else:
            raise DataUnavailableError("The provided URL does not point to a direct CSV/TSV file.")
    except requests.exceptions.RequestException as e:
        raise DataUnavailableError(f"Failed to download serology metadata from {url}: {str(e)}")
    except pd.errors.EmptyDataError:
        raise DataUnavailableError("The downloaded file is empty.")
