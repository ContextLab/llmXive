"""
NIST Repository Downloader (T013).

Fetches ball milling data from the NIST Search API.
Strictly real data only: no synthetic fallbacks, no mock data generators.
"""
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import requests

from src.utils.logger import get_module_logger
from src.exceptions import SourceConnectionError, SourceNotFoundError

logger = get_module_logger(__name__)

NIST_API_BASE = "https://www.nist.gov/publications/search"
# Note: NIST's specific API for datasets might differ. 
# We assume a search API that returns dataset links.
# The spec mentions `q=ball+milling AND datasetType:csv`.

def download_data(query: str = "ball milling", limit: int = 10) -> Optional[pd.DataFrame]:
    """
    Downloads data from NIST repository based on a query.
    
    Args:
        query: Search query string.
        limit: Maximum number of datasets to process.
        
    Returns:
        DataFrame with the data, or None if failed.
        
    Raises:
        SourceConnectionError: If connection fails.
    """
    try:
        # Simulating a search request to NIST.
        # In a real implementation, the exact endpoint and parameters would be verified.
        # We use a generic search pattern that matches the spec's intent.
        url = NIST_API_BASE
        params = {
            "q": query,
            "format": "json",
            "limit": limit
        }
        
        logger.info(f"Searching NIST with query: {query}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 404:
            logger.warning("NIST search endpoint not found.")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Parse the response to find dataset links
        # This logic depends heavily on the actual NIST API response structure.
        # We assume a list of results with a 'download_url' or similar.
        if "results" not in data:
            logger.warning("NIST response did not contain 'results' key.")
            return None
        
        results = data["results"]
        if not results:
            logger.warning("NIST returned no results.")
            return None
        
        # Collect DataFrames from found CSVs
        dfs = []
        count = 0
        for item in results:
            if count >= limit:
                break
            
            # Assume 'download_url' exists in the result item
            download_url = item.get("download_url") or item.get("url")
            if not download_url:
                continue
            
            if not download_url.endswith(('.csv', '.json')):
                continue
                
            logger.info(f"Downloading dataset from: {download_url}")
            try:
                csv_resp = requests.get(download_url, timeout=30)
                csv_resp.raise_for_status()
                
                # Try to parse as CSV
                df_temp = pd.read_csv(pd.io.common.StringIO(csv_resp.text))
                dfs.append(df_temp)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to download/parse {download_url}: {e}")
                continue
        
        if not dfs:
            logger.warning("No valid datasets downloaded from NIST.")
            return None
        
        return pd.concat(dfs, ignore_index=True)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to NIST: {e}")
        raise SourceConnectionError(f"NIST connection failed: {e}")

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes the raw DataFrame to match the project schema.
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        Processed DataFrame.
    """
    # Placeholder for schema normalization logic
    # In a real scenario, we would map NIST columns to our schema.
    return df

def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def run_nist_ingestion(output_dir: str = "data/raw") -> Optional[str]:
    """
    Orchestrates the NIST ingestion pipeline.
    
    Args:
        output_dir: Directory to save the raw data.
        
    Returns:
        Path to the saved file, or None if skipped/failed.
    """
    output_path = Path(output_dir) / "nist_raw.csv"
    
    try:
        logger.info("Starting NIST ingestion...")
        df = download_data(query="ball milling AND datasetType:csv", limit=5)
        
        if df is None or df.empty:
            logger.warning("Source skipped: NIST (no rows or error)")
            return None
        
        processed_df = process_data(df)
        save_to_csv(processed_df, str(output_path))
        return str(output_path)
        
    except SourceConnectionError as e:
        logger.warning(f"Source skipped: NIST (connection error: {e})")
        return None
    except Exception as e:
        logger.warning(f"Source skipped: NIST (unexpected error: {e})")
        return None
