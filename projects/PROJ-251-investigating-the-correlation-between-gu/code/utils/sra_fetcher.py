import os
import sys
import logging
import requests
from pathlib import Path
from typing import Tuple, Optional
from .config import get_sra_accession, get_raw_path, get_hf_token, get_ncbi_api_key
from .logging_config import get_logger
from .sra_downloader import DataUnavailableError

# Define the verified real data source as per project constraints.
# The project uses a specific HuggingFace dataset that contains the pre-processed
# OTU tables and serology metadata for the SRP accession series.
# This is the "VERIFIED REAL DATA SOURCE" referenced in the system prompt.
HF_DATASET_NAME = "gut-microbiome-influenza-vaccination/preprocessed"
OTU_FILE_NAME = "otutable.csv"
SEROLOGY_FILE_NAME = "serology.csv"

def fetch_huggingface_data(dataset_name: str, output_dir: Path, hf_token: Optional[str] = None) -> Tuple[Path, Path]:
    """
    Fetches pre-processed data from HuggingFace Datasets.
    
    This function attempts to download the specific CSV files containing the
    OTU table and serology metadata. It does NOT fall back to synthetic data.
    If the download fails, it raises DataUnavailableError.
    
    Args:
        dataset_name: The HuggingFace dataset identifier.
        output_dir: Directory to save the downloaded files.
        hf_token: Optional HuggingFace token for private datasets.
        
    Returns:
        Tuple of (path_to_otu, path_to_serology)
        
    Raises:
        DataUnavailableError: If the dataset cannot be fetched.
    """
    logger = get_logger(__name__)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    otu_path = output_dir / OTU_FILE_NAME
    serology_path = output_dir / SEROLOGY_FILE_NAME
    
    try:
        # Attempt to load the dataset using the datasets library
        # This is the standard way to fetch real data from HuggingFace
        from datasets import load_dataset
        
        logger.info(f"Attempting to load dataset: {dataset_name}")
        
        # Load the dataset. We assume the dataset is structured with 'otutable' and 'serology'
        # splits or files. If the dataset structure is different, this needs adjustment.
        # Based on typical project structures, we assume the dataset contains these two files.
        
        # Strategy: Try to load the dataset and check for the specific files.
        # If the dataset is a repository with CSV files, we can download them directly.
        
        # For robustness, we will try to download the files directly if they exist
        # in the dataset repository.
        
        # Check if the dataset exists and is accessible
        try:
            ds = load_dataset(dataset_name, split="train", streaming=True)
            logger.info(f"Dataset {dataset_name} is accessible.")
        except Exception as e:
            logger.error(f"Dataset {dataset_name} not accessible: {e}")
            raise DataUnavailableError(f"Dataset {dataset_name} not found or accessible: {e}")
        
        # Since we need specific CSV files, we will construct the direct download URLs
        # assuming the dataset is hosted on HuggingFace Hub.
        # The URL pattern is: https://huggingface.co/datasets/{user}/{repo}/resolve/main/{file}
        
        # We need to find the actual repository name. 
        # For this task, we assume the dataset is available at a known public URL
        # or we use the datasets library to fetch the files.
        
        # Let's try a direct approach: download the files from the HuggingFace Hub.
        # We assume the files are at the root of the dataset.
        
        base_url = f"https://huggingface.co/datasets/{dataset_name.replace('/', '/')}/resolve/main"
        # Note: The dataset_name format is "user/repo", so we need to construct the URL correctly.
        # The correct format for the URL is:
        # https://huggingface.co/datasets/{user}/{repo}/resolve/main/{filename}
        
        # Split the dataset name
        parts = dataset_name.split('/')
        if len(parts) != 2:
            raise DataUnavailableError(f"Invalid dataset name format: {dataset_name}")
        
        user, repo = parts
        base_url = f"https://huggingface.co/datasets/{user}/{repo}/resolve/main"
        
        otu_url = f"{base_url}/{OTU_FILE_NAME}"
        serology_url = f"{base_url}/{SEROLOGY_FILE_NAME}"
        
        headers = {}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
        
        # Download OTU table
        logger.info(f"Downloading OTU table from: {otu_url}")
        response = requests.get(otu_url, headers=headers, timeout=300)
        if response.status_code == 404:
            raise DataUnavailableError(f"OTU table not found at {otu_url}")
        response.raise_for_status()
        with open(otu_path, 'wb') as f:
            f.write(response.content)
        
        # Download Serology metadata
        logger.info(f"Downloading Serology metadata from: {serology_url}")
        response = requests.get(serology_url, headers=headers, timeout=300)
        if response.status_code == 404:
            raise DataUnavailableError(f"Serology metadata not found at {serology_url}")
        response.raise_for_status()
        with open(serology_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded {otu_path} and {serology_path}")
        return otu_path, serology_path
        
    except DataUnavailableError:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch data from HuggingFace: {e}")
        raise DataUnavailableError(f"Failed to fetch real data from HuggingFace: {e}")

def main():
    """
    Main entry point for Strategy A data fetching.
    """
    logger = get_logger(__name__)
    
    # Get configuration
    sra_accession = get_sra_accession()
    if not sra_accession:
        # If no specific accession is set, we might use a default or fail.
        # For this task, we assume the dataset name is fixed as per the verified source.
        # The SRA accession is used for logging/context, but the actual data source
        # is the HuggingFace dataset.
        logger.warning("SRA_ACCESSION not set in config. Using default dataset.")
    
    raw_path = get_raw_path()
    raw_path.mkdir(parents=True, exist_ok=True)
    
    hf_token = get_hf_token()
    
    try:
        otu_path, serology_path = fetch_huggingface_data(HF_DATASET_NAME, raw_path, hf_token)
        logger.info(f"Strategy A completed. Output: {otu_path}, {serology_path}")
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during fetch: {e}")
        raise

if __name__ == "__main__":
    main()
