import os
import logging
from pathlib import Path
from typing import Optional, Tuple
import requests
import pandas as pd
import json

from utils.logging_config import get_logger

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when real data cannot be fetched from the source."""
    pass

def _get_download_url(accession: str, file_type: str) -> str:
    """
    Constructs the URL for downloading pre-processed data.
    In a real production environment, this would query a database or API
    to find the exact URL for the pre-processed files associated with the accession.
    For this implementation, we simulate a lookup or attempt a standard pattern.
    
    We assume the data is hosted on a public repository (e.g., Figshare/Zenodo) 
    linked to the SRA study.
    """
    # Simulating a lookup table for known studies with pre-processed data
    # In reality, this would be dynamic or fetched from an API
    known_studies = {
        "SRP123456": {
            "otu": "https://example-repo.org/data/SRP123456/otu_table.csv",
            "serology": "https://example-repo.org/data/SRP123456/serology.csv"
        },
        # Add more known studies as needed
    }
    
    if accession in known_studies:
        if file_type == "otu":
            return known_studies[accession]["otu"]
        elif file_type == "serology":
            return known_studies[accession]["serology"]
    
    # Fallback: Try to construct a generic URL if a pattern is known
    # This is a placeholder for real logic
    base_url = f"https://example-repo.org/studies/{accession}"
    if file_type == "otu":
        return f"{base_url}/otu_table.csv"
    elif file_type == "serology":
        return f"{base_url}/serology.csv"
        
    raise DataUnavailableError(f"No download URL found for accession {accession}")

def fetch_otu_table(accession: str, output_path: str) -> None:
    """
    Fetches the pre-processed OTU table for a given accession.
    
    Args:
        accession: The SRA accession ID (e.g., SRP123456).
        output_path: Path where the CSV will be saved.
        
    Raises:
        DataUnavailableError: If the data cannot be fetched.
    """
    try:
        url = _get_download_url(accession, "otu")
        logger.info(f"Downloading OTU table from {url}")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Save content to file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Validate basic structure
        df = pd.read_csv(output_path)
        if df.empty:
            raise DataUnavailableError("OTU table is empty.")
        if 'subject_id' not in df.columns:
            # Try to infer or raise error if strict schema is required
            logger.warning("OTU table does not contain 'subject_id' column. Checking for alternatives...")
            # In a real scenario, we might try to map columns or fail
            if 'SampleID' in df.columns:
                df.rename(columns={'SampleID': 'subject_id'}, inplace=True)
                df.to_csv(output_path, index=False)
            else:
                raise DataUnavailableError("OTU table missing 'subject_id' column.")
                
        logger.info(f"OTU table saved to {output_path} with {len(df)} rows.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download OTU table: {e}")
        raise DataUnavailableError(f"Network error fetching OTU table: {e}")
    except pd.errors.EmptyDataError:
        raise DataUnavailableError("OTU table file is empty.")
    except Exception as e:
        logger.error(f"Error processing OTU table: {e}")
        raise DataUnavailableError(f"Error processing OTU table: {e}")

def fetch_serology_metadata(accession: str, output_path: str) -> None:
    """
    Fetches the serology metadata for a given accession.
    
    Args:
        accession: The SRA accession ID.
        output_path: Path where the CSV will be saved.
        
    Raises:
        DataUnavailableError: If the data cannot be fetched.
    """
    try:
        url = _get_download_url(accession, "serology")
        logger.info(f"Downloading serology metadata from {url}")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Save content to file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Validate basic structure
        df = pd.read_csv(output_path)
        if df.empty:
            raise DataUnavailableError("Serology metadata is empty.")
        required_cols = ['subject_id', 'titer_baseline', 'titer_post']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DataUnavailableError(f"Serology metadata missing columns: {missing_cols}")
                
        logger.info(f"Serology metadata saved to {output_path} with {len(df)} rows.")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download serology metadata: {e}")
        raise DataUnavailableError(f"Network error fetching serology metadata: {e}")
    except pd.errors.EmptyDataError:
        raise DataUnavailableError("Serology metadata file is empty.")
    except Exception as e:
        logger.error(f"Error processing serology metadata: {e}")
        raise DataUnavailableError(f"Error processing serology metadata: {e}")

def fetch_huggingface_data(dataset_id: str, split: str = "train") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Alternative fetch method using HuggingFace datasets if available.
    This is a fallback if direct SRA links are not usable.
    """
    try:
        from datasets import load_dataset
        ds = load_dataset(dataset_id, split=split)
        # Assuming specific column names in HF dataset
        # Adjust based on actual dataset schema
        otu_df = ds.to_pandas() # Simplified
        # In reality, this would require specific mapping
        return otu_df, pd.DataFrame() 
    except ImportError:
        raise DataUnavailableError("datasets library not installed for HF fetch.")
    except Exception as e:
        raise DataUnavailableError(f"HF fetch failed: {e}")
