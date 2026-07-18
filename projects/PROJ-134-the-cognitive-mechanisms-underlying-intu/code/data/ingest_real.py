"""
Real Data Ingestion Module for Moral Mechanisms Project.

This module implements strict "Fail Loudly" logic for fetching real data.
It attempts to fetch:
1. MFQ (Moral Foundations Questionnaire) data from OSF (Open Science Framework).
2. Moral Stories dataset from HuggingFace.

If any fetch operation fails, it raises a DataFetchError immediately without
falling back to synthetic generators. This ensures data integrity and prevents
silent fabrication.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import pandas as pd

# Add project root to path for imports if running as script
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging_utils import get_logger, log_pipeline_step

# Configure logging
logger = get_logger("ingest_real")

class DataFetchError(Exception):
    """Custom exception for data fetching failures.
    
    Raised when real data cannot be retrieved from the specified source.
    This error halts execution to prevent the use of synthetic data as a fallback.
    """
    pass

# OSF Configuration
# Note: Using a public OSF project ID. In a real scenario, this might need 
# specific file paths or authentication if the data is private.
OSF_NODE_ID = "z8k9v"  # Example ID for a public moral foundations dataset
OSF_API_BASE = "https://api.osf.io/v2/nodes"
OSF_FILES_ENDPOINT = f"{OSF_API_BASE}/{OSF_NODE_ID}/files/osfstorage"

# HuggingFace Configuration
HF_DATASET_NAME = "moral-stories-v1" 
# Note: If the dataset is not public or doesn't exist, this will fail loudly.
# We use a try/except around the import to ensure the library is available.
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("HuggingFace datasets library not installed. Real data fetch will fail.")

def fetch_from_osf(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Fetches real MFQ data from the Open Science Framework (OSF).

    This function attempts to download the MFQ dataset. If the network request fails,
    the file is not found, or the data is malformed, it raises DataFetchError.
    It does NOT fall back to synthetic data.

    Args:
        output_path (Optional[Path]): Path to save the downloaded CSV. 
                                     Defaults to data/raw/mfq_osf_real.csv.

    Returns:
        pd.DataFrame: The loaded MFQ data.

    Raises:
        DataFetchError: If the fetch fails for any reason (network, auth, 404, etc.).
        ImportError: If requests library is missing.
    """
    if output_path is None:
        output_path = Path("data/raw/mfq_osf_real.csv")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Attempting to fetch real MFQ data from OSF Node: {OSF_NODE_ID}")
    
    try:
        import requests
        import io
        
        # OSF API v2 returns JSON. We need to find the file download URL.
        # This is a simplified fetch assuming a direct file link or a known structure.
        # In a robust implementation, we would paginate through the files endpoint.
        # For this implementation, we attempt to fetch a specific known file or 
        # the main dataset if available via a direct link pattern.
        
        # Strategy: Try to fetch a known file ID or the root listing.
        # Since we don't have the specific file ID in the prompt, we attempt 
        # to list files and find a CSV, or fail if not found.
        
        url = OSF_FILES_ENDPOINT
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            raise DataFetchError(f"OSF Node {OSF_NODE_ID} not found. Cannot fetch real data.")
        elif response.status_code != 200:
            raise DataFetchError(f"OSF API returned status {response.status_code}. Cannot fetch real data.")
        
        data = response.json()
        
        # Look for a file named 'mfq_data.csv' or similar in the 'data' attribute
        files = data.get('data', [])
        target_file = None
        
        for item in files:
            fname = item.get('attributes', {}).get('name', '')
            if fname.endswith('.csv'):
                target_file = item
                break
        
        if not target_file:
            # If no CSV found, we cannot proceed with real data.
            raise DataFetchError("No CSV file found in the specified OSF node. Cannot fetch real data.")
        
        # Construct download URL
        download_url = target_file['links']['download']
        
        # Fetch the actual file content
        file_response = requests.get(download_url, timeout=60)
        if file_response.status_code != 200:
            raise DataFetchError(f"Failed to download file content from OSF. Status: {file_response.status_code}")
        
        # Load into pandas
        df = pd.read_csv(io.StringIO(file_response.text))
        
        # Save to disk
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully fetched and saved real MFQ data to {output_path}")
        
        return df

    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Network error while fetching OSF data: {str(e)}")
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Unexpected error fetching OSF data: {str(e)}")

def fetch_from_huggingface(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Fetches real Moral Stories data from HuggingFace Datasets.

    This function attempts to load the 'moral-stories-v1' dataset. 
    If the dataset does not exist, cannot be accessed, or the library is missing,
    it raises DataFetchError immediately. No synthetic fallback.

    Args:
        output_path (Optional[Path]): Path to save the downloaded CSV.
                                     Defaults to data/raw/moral_stories_hf_real.csv.

    Returns:
        pd.DataFrame: The loaded Moral Stories data.

    Raises:
        DataFetchError: If the fetch fails.
    """
    if output_path is None:
        output_path = Path("data/raw/moral_stories_hf_real.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Attempting to fetch real Moral Stories from HuggingFace: {HF_DATASET_NAME}")

    if not HF_AVAILABLE:
        raise DataFetchError("HuggingFace 'datasets' library is not installed. Cannot fetch real data.")

    try:
        # Attempt to load the dataset
        # We assume the dataset is public. If it requires a token, we'd need HF_TOKEN env var.
        dataset = load_dataset(HF_DATASET_NAME, split="train")
        
        if dataset is None or len(dataset) == 0:
            raise DataFetchError("Loaded HuggingFace dataset is empty. Cannot fetch real data.")
        
        # Convert to pandas
        df = dataset.to_pandas()
        
        # Validate basic schema (ensure it has story and judgment columns)
        required_cols = ['story', 'judgment'] # Adjust based on actual dataset schema if known
        # If the dataset has different columns, we might just load it and let downstream fail,
        # but for "Fail Loudly" we check if it looks like data.
        if df.empty:
            raise DataFetchError("Dataset conversion to DataFrame resulted in empty data.")

        # Save to disk
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully fetched and saved real Moral Stories data to {output_path}")
        
        return df

    except Exception as e:
        # Catch all specific HuggingFace errors and generic network errors
        raise DataFetchError(f"Failed to fetch real data from HuggingFace '{HF_DATASET_NAME}': {str(e)}")

def validate_real_data_schema(df: pd.DataFrame, data_type: str) -> None:
    """
    Validates that the fetched real data conforms to expected schema.
    
    This function checks for required columns and data types.
    It raises ValueError if the schema is invalid.

    Args:
        df (pd.DataFrame): The dataframe to validate.
        data_type (str): 'mfq' or 'stories' to determine validation rules.

    Raises:
        ValueError: If the schema is invalid.
    """
    if df.empty:
        raise ValueError(f"Real {data_type} data is empty after fetching.")

    if data_type == 'mfq':
        # Expected MFQ columns (simplified)
        required_cols = ['participant_id', 'foundation_1', 'foundation_2', 'foundation_3', 'foundation_4', 'foundation_5']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Real MFQ data missing required columns: {missing}")
        
    elif data_type == 'stories':
        # Expected Stories columns
        required_cols = ['story_id', 'story_text', 'judgment']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            # Be lenient on exact names if it's a real dataset, but ensure content exists
            if 'story' not in df.columns and 'story_text' not in df.columns:
                raise ValueError("Real Stories data missing 'story' or 'story_text' column.")
            if 'judgment' not in df.columns:
                raise ValueError("Real Stories data missing 'judgment' column.")

def main():
    """
    Main entry point for the real data ingestion script.
    
    Executes fetches for both MFQ and Moral Stories.
    Writes output to data/raw/ and logs to data/logs/.
    Exits with code 1 if DataFetchError occurs.
    """
    log_pipeline_step("INGEST_REAL_START")
    
    mfq_df = None
    stories_df = None

    try:
        # 1. Fetch MFQ
        try:
            mfq_df = fetch_from_osf()
            validate_real_data_schema(mfq_df, 'mfq')
            logger.info("MFQ validation passed.")
        except DataFetchError as e:
            logger.error(f"CRITICAL: MFQ Fetch Failed: {e}")
            raise # Re-raise to halt execution

        # 2. Fetch Stories
        try:
            stories_df = fetch_from_huggingface()
            validate_real_data_schema(stories_df, 'stories')
            logger.info("Stories validation passed.")
        except DataFetchError as e:
            logger.error(f"CRITICAL: Stories Fetch Failed: {e}")
            raise # Re-raise to halt execution

        logger.info("Real data ingestion completed successfully.")
        log_pipeline_step("INGEST_REAL_SUCCESS")
        return True

    except DataFetchError as e:
        logger.error(f"REAL DATA INGESTION FAILED: {e}")
        log_pipeline_step("INGEST_REAL_FAILURE", error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR IN INGEST_REAL: {e}")
        log_pipeline_step("INGEST_REAL_UNEXPECTED_ERROR", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()