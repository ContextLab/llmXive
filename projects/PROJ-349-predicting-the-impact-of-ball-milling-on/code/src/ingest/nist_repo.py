"""
NIST Repository Data Downloader.

Fetches ball milling data from the NIST Search API.
Strictly uses real data. No synthetic fallbacks.
"""
import logging
import os
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError, DataIngestionError

logger = get_module_logger(__name__)

NIST_SEARCH_API = "https://data.nist.gov/api/v1/search"

def download_data(query: str = "ball milling", dataset_type: str = "csv", timeout: int = 60) -> Optional[pd.DataFrame]:
    """
    Downloads data from NIST Search API.

    Args:
        query: Search query string.
        dataset_type: Type of dataset to filter (e.g., 'csv').
        timeout: Request timeout in seconds.

    Returns:
        DataFrame containing the downloaded data, or None if failed.
    """
    headers = {
        "Accept": "application/json"
    }

    params = {
        "q": f"{query} AND datasetType:{dataset_type}",
        "limit": 10,
        "offset": 0
    }

    try:
        logger.info(f"Searching NIST for: {params['q']}")
        response = requests.get(NIST_SEARCH_API, headers=headers, params=params, timeout=timeout)

        if response.status_code != 200:
            logger.warning(f"NIST API returned status {response.status_code}: {response.text}")
            return None

        data = response.json()
        
        if "results" not in data or not data["results"]:
            logger.warning("NIST search returned 0 results.")
            return None

        # Assume the first result is the most relevant
        first_result = data["results"][0]
        download_url = first_result.get("downloadUrl")
        
        if not download_url:
            logger.warning("No download URL found in NIST result.")
            return None

        logger.info(f"Downloading data from: {download_url}")
        download_response = requests.get(download_url, timeout=timeout)
        
        if download_response.status_code != 200:
            logger.warning(f"Failed to download data from NIST: {download_response.status_code}")
            return None

        # Try to parse as CSV
        try:
            df = pd.read_csv(pd.io.common.StringIO(download_response.text))
            logger.info(f"Successfully downloaded {len(df)} rows from NIST.")
            return df
        except Exception as e:
            logger.error(f"Failed to parse NIST data as CSV: {e}")
            return None

    except requests.exceptions.Timeout:
        logger.warning("NIST API request timed out.")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("NIST API connection failed.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading NIST data: {e}")
        raise SourceConnectionError(f"Failed to download NIST data: {e}")

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the downloaded DataFrame to match the project schema.

    Args:
        df: Raw DataFrame from NIST.

    Returns:
        Processed DataFrame.
    """
    # Placeholder for schema mapping logic
    # In a real scenario, this would map NIST columns to our expected schema
    required_cols = [
        "experiment_id", "source", "material_type", "milling_speed", 
        "milling_time", "ball_to_powder_ratio", "youngs_modulus", 
        "density", "d10", "d50", "d90", "process_duration"
    ]
    
    # Add missing columns with NaN
    for col in required_cols:
        if col not in df.columns:
            df[col] = float('nan')
    
    df['source'] = 'nist'
    
    # Ensure experiment_id exists
    if 'experiment_id' not in df.columns or df['experiment_id'].isna().all():
        df['experiment_id'] = [f"nist_{i}" for i in range(len(df))]

    return df

def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves DataFrame to CSV.

    Args:
        df: DataFrame to save.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} entries to {output_path}")

def run_nist_ingestion(output_dir: str = "data/raw") -> Optional[str]:
    """
    Orchestrates the NIST data ingestion.

    Args:
        output_dir: Directory to save the raw data.

    Returns:
        Path to the saved CSV file, or None if no data was fetched.
    """
    output_path = os.path.join(output_dir, "nist_raw.csv")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    raw_df = download_data()

    if raw_df is None or raw_df.empty:
        logger.warning("Source skipped: NIST (no rows or error)")
        return None

    processed_df = process_data(raw_df)
    save_to_csv(processed_df, output_path)
    return output_path
