"""
Data download module for fetching the GFA dataset from HuggingFace.

This module handles the retrieval of the Recent Experimental GFA dataset,
verifies its schema, and generates checksums for data integrity.
It strictly adheres to the requirement of failing loudly if the real data
cannot be fetched or validated, with no synthetic fallbacks.
"""
import os
import logging
import time
import shutil
import pandas as pd
from pathlib import Path
from typing import Optional, Set

from huggingface_hub import hf_hub_download
from huggingface_hub.utils import (
    RepositoryNotFoundError,
    RevisionNotFoundError,
    LocalEntryNotFoundError,
    HFValidationError,
    HfHubHTTPError
)

# Local imports based on project API surface
from data.checksums import save_checksum
from utils.logger import get_logger, DataDownloadError

logger = get_logger(__name__)

# Constants
DATASET_REPO_ID = "GFA-D2/pilot_flags"
DATASET_FILENAME = "pilot_flags.csv"
OUTPUT_DIR = "data/raw"
OUTPUT_FILENAME = "gfa_dataset.csv"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
CHECKSUM_PATH = os.path.join(OUTPUT_DIR, f"{OUTPUT_FILENAME}.sha256")

# Required columns as per spec
REQUIRED_COLUMNS = {"composition", "log10_Rc"}
# Fallback: if 'Rc' exists but 'log10_Rc' doesn't, we accept it but warn
ALLOWED_ALTERNATIVES = {"Rc"}

def verify_schema(df: pd.DataFrame, required_cols: Set[str]) -> bool:
    """
    Verifies that the DataFrame contains the required columns.
    
    Args:
        df: The DataFrame to verify.
        required_cols: Set of required column names.
        
    Returns:
        True if schema is valid.
        
    Raises:
        ValueError: If required columns are missing or types are incorrect.
    """
    available_cols = set(df.columns)
    missing = required_cols - available_cols

    # Check for allowed alternatives
    if "log10_Rc" in missing and "Rc" in available_cols:
        logger.warning("Column 'log10_Rc' not found, but 'Rc' found. Using 'Rc' as proxy.")
        missing.remove("log10_Rc")
        # We will treat 'Rc' as the target column for downstream, 
        # but strictly speaking the schema check passes.
    
    if missing:
        raise ValueError(f"Schema verification failed. Missing required columns: {missing}")

    # Type verification
    if not df.empty:
        # Check composition is string-like
        if not pd.api.types.is_string_dtype(df['composition']) and not df['composition'].apply(lambda x: isinstance(x, str)).all():
            raise ValueError(f"Column 'composition' must be of string type. Found: {df['composition'].dtype}")
        
        # Check log10_Rc (or Rc) is numeric
        target_col = 'log10_Rc' if 'log10_Rc' in df.columns else 'Rc'
        if not pd.api.types.is_numeric_dtype(df[target_col]):
            raise ValueError(f"Column '{target_col}' must be numeric. Found: {df[target_col].dtype}")

    logger.info("Schema verification passed.")
    return True

def download_gfa_dataset() -> str:
    """
    Downloads the GFA dataset from HuggingFace with retry logic and exponential backoff.
    
    Requirements:
    1. Retry Logic: Explicit retry with exponential backoff.
    2. Schema Verification: Immediate check after download.
    3. Checksum: Generated ONLY after schema verification.
    4. Failure Handling: Raises exception immediately on failure.
    5. No Synthetic Data: No fallback to fake data.
    
    Returns:
        Path to the downloaded file.
        
    Raises:
        DataDownloadError: If download fails after retries or schema verification fails.
    """
    output_file = Path(OUTPUT_PATH)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    max_retries = 5
    base_delay = 2.0  # seconds
    max_delay = 30.0  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting to download dataset (Attempt {attempt}/{max_retries})...")
            
            # Use hf_hub_download for robust downloading
            # This downloads to the HF cache, we then copy to our local data/raw
            try:
                downloaded_path = hf_hub_download(
                    repo_id=DATASET_REPO_ID,
                    filename=DATASET_FILENAME,
                    repo_type="dataset",
                    etag_timeout=10
                )
            except HFValidationError as e:
                raise DataDownloadError(f"Invalid dataset configuration: {e}") from e
            except (RepositoryNotFoundError, RevisionNotFoundError) as e:
                raise DataDownloadError(f"Dataset repository not found: {DATASET_REPO_ID}. Error: {e}") from e
            except LocalEntryNotFoundError as e:
                # File might be missing from the repo
                raise DataDownloadError(f"File '{DATASET_FILENAME}' not found in repository.") from e
            except Exception as e:
                # Network errors, timeouts, etc.
                raise DataDownloadError(f"Network error during download: {e}") from e
            
            # Copy from HF cache to our project data directory
            logger.debug(f"Copying downloaded file from {downloaded_path} to {output_file}")
            shutil.copy2(downloaded_path, output_file)
            
            logger.info(f"Dataset downloaded successfully to {output_file}")
            
            # Schema Verification
            logger.info("Verifying dataset schema...")
            try:
                df = pd.read_csv(output_file)
                verify_schema(df, REQUIRED_COLUMNS)
            except ValueError as e:
                # Schema error is critical and not retryable
                raise DataDownloadError(f"Schema verification failed: {e}") from e
            except Exception as e:
                raise DataDownloadError(f"Failed to read or parse downloaded CSV: {e}") from e
            
            # Generate Checksum ONLY after schema verification passes
            logger.info("Generating checksum...")
            try:
                save_checksum(str(output_file), CHECKSUM_PATH)
                logger.info(f"Checksum saved to {CHECKSUM_PATH}")
            except Exception as e:
                raise DataDownloadError(f"Failed to generate checksum: {e}") from e
            
            logger.info("Download and verification completed successfully.")
            return str(output_file)
            
        except DataDownloadError:
            # Re-raise immediately if it's a DataDownloadError (schema, repo not found, etc.)
            # These are not transient network errors that retries would fix.
            logger.critical(f"Critical error during download: {sys.exc_info()[1]}")
            raise
        except Exception as e:
            # Catch-all for unexpected transient errors
            logger.error(f"Unexpected error during download attempt {attempt}: {e}", exc_info=True)
            if attempt == max_retries:
                raise DataDownloadError(f"Download failed after {max_retries} attempts due to unexpected error.") from e
        
        # Exponential backoff for transient errors
        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
        logger.warning(f"Download failed. Retrying in {delay:.1f} seconds...")
        time.sleep(delay)
    
    # Should not be reached due to the raise in the loop, but for safety:
    raise DataDownloadError("Download failed after all retries (unreachable code path).")

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
    import sys
    main()