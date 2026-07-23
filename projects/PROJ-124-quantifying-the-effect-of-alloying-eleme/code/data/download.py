"""
Data download module for fetching the GFA dataset from HuggingFace.

This module handles the retrieval of the Recent Experimental GFA dataset,
verifies its schema, and generates checksums for data integrity.
"""
import os
import logging
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import RepositoryNotFoundError, RevisionNotFoundError, LocalEntryNotFoundError

# Local imports based on project API surface
from data.checksums import save_checksum
from utils.logger import get_logger, DataDownloadError

logger = get_logger(__name__)

# Constants
DATASET_REPO_ID = "GFA-D2/pilot_flags"
DATASET_FILENAME = "pilot_flags.csv"  # Assuming the file is named this on HF
OUTPUT_PATH = "data/raw/gfa_dataset.csv"
CHECKSUM_PATH = "data/raw/gfa_dataset.csv.sha256"
REQUIRED_COLUMNS = {"composition", "log10_Rc"}  # Or "Rc" as fallback

def verify_schema(df: pd.DataFrame, required_cols: set) -> bool:
    """
    Verifies that the DataFrame contains the required columns.
    
    Args:
        df: The DataFrame to verify.
        required_cols: Set of required column names.
        
    Returns:
        True if schema is valid.
        
    Raises:
        ValueError: If required columns are missing.
    """
    available_cols = set(df.columns)
    missing = required_cols - available_cols
    
    # Check if "Rc" is present as an alternative to "log10_Rc"
    if "log10_Rc" in missing and "Rc" in available_cols:
        logger.info("Column 'log10_Rc' not found, but 'Rc' found. Schema is acceptable.")
        return True
        
    if missing:
        raise ValueError(f"Schema verification failed. Missing required columns: {missing}")
    
    logger.info("Schema verification passed.")
    return True

def download_gfa_dataset() -> str:
    """
    Downloads the GFA dataset from HuggingFace with retry logic.
    
    Returns:
        Path to the downloaded file.
        
    Raises:
        DataDownloadError: If download fails after retries or schema verification fails.
    """
    output_file = Path(OUTPUT_PATH)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    max_retries = 3
    base_delay = 5.0  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting to download dataset (Attempt {attempt}/{max_retries})...")
            
            # Use hf_hub_download for robust downloading
            # We assume the file is at the root of the dataset repo
            downloaded_path = hf_hub_download(
                repo_id=DATASET_REPO_ID,
                filename=DATASET_FILENAME,
                repo_type="dataset"
            )
            
            # Move/copy to our expected output path if needed, 
            # or just use the downloaded path if it matches expectations.
            # hf_hub_download returns the path in the HF cache. 
            # We need to copy it to data/raw/ as per task requirement.
            import shutil
            shutil.copy(downloaded_path, output_file)
            
            logger.info(f"Dataset downloaded successfully to {output_file}")
            
            # Schema Verification
            logger.info("Verifying dataset schema...")
            df = pd.read_csv(output_file)
            verify_schema(df, REQUIRED_COLUMNS)
            
            # Generate Checksum ONLY after schema verification passes
            logger.info("Generating checksum...")
            save_checksum(str(output_file), CHECKSUM_PATH)
            logger.info(f"Checksum saved to {CHECKSUM_PATH}")
            
            return str(output_file)
            
        except (RepositoryNotFoundError, RevisionNotFoundError) as e:
            logger.error(f"Repository or revision not found: {e}")
            raise DataDownloadError(f"Failed to access dataset repository: {e}") from e
        except LocalEntryNotFoundError as e:
            logger.error(f"Local entry not found (network issue or file missing): {e}")
            if attempt == max_retries:
                raise DataDownloadError("Download failed after all retries due to network or file issues.") from e
        except Exception as e:
            logger.error(f"Error during download attempt {attempt}: {e}")
            if attempt == max_retries:
                raise DataDownloadError(f"Download failed after {max_retries} attempts.") from e
        
        # Exponential backoff
        delay = base_delay * (2 ** (attempt - 1))
        logger.warning(f"Download failed. Retrying in {delay:.1f} seconds...")
        time.sleep(delay)
    
    raise DataDownloadError("Download failed after all retries.")

def main():
    """Main entry point for standalone execution."""
    try:
        path = download_gfa_dataset()
        logger.info(f"Task completed. Data available at: {path}")
    except DataDownloadError as e:
        logger.critical(f"Task failed: {e}")
        exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()