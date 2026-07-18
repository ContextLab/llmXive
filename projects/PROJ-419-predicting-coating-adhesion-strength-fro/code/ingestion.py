import os
import time
import logging
from typing import Optional, List, Dict, Any
import requests
import pandas as pd
import json

from config import main as config_main
from utils import DataGapError, APIError, verify_url_accessibility, exponential_backoff

logger = logging.getLogger("llmXive")

# Constants
ASTM_D4541_KEYWORDS = [
    "ASTM D4541", "ASTM4541", "Pull-off", "pull-off", "Pull Off", "pull off",
    "D4541", "pull-off strength", "adhesion strength", "pull-off test"
]

def validate_url_parameter(url: Optional[str]) -> None:
    if not url or not isinstance(url, str):
        raise DataGapError("Invalid or missing URL parameter")
    if not url.startswith(("http://", "https://")):
        raise DataGapError(f"Invalid URL scheme: {url}")

@exponential_backoff
def fetch_materials_project_data(api_key: str, endpoint: str) -> Dict[str, Any]:
    """Fetch data from Materials Project API."""
    validate_url_parameter(endpoint)
    headers = {"X-API-Key": api_key}
    try:
        response = requests.get(endpoint, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Materials Project API error: {e}")

@exponential_backoff
def fetch_nist_surface_metrology_data(url: str) -> Dict[str, Any]:
    """Fetch data from NIST Surface Metrology Repository."""
    validate_url_parameter(url)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"NIST API error: {e}")

def fetch_open_access_literature_data(url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Fetch data from open access literature sources."""
    validate_url_parameter(url)
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Literature API error: {e}")

def filter_astm_d4541_records(df: pd.DataFrame, test_method_col: str = "test_method") -> pd.DataFrame:
    """
    Filter records strictly to ASTM D4541 pull-off test results.
    
    Logic:
    1. Check if the specified column exists. If not, log and return empty DF or raise.
    2. Normalize the column values to lowercase strings.
    3. Check if any value in the row matches any of the ASTM D4541 keywords.
    4. Return the filtered DataFrame.
    
    FR-009: Strict filtering to ASTM D4541.
    """
    if test_method_col not in df.columns:
        logger.warning(f"Column '{test_method_col}' not found in dataset. Returning empty DataFrame.")
        return pd.DataFrame()
    
    # Normalize column to string and lowercase for comparison
    df_test_method = df[test_method_col].astype(str).str.lower()
    
    # Create a mask for rows matching any keyword
    mask = df_test_method.apply(
        lambda x: any(keyword.lower() in x for keyword in ASTM_D4541_KEYWORDS)
    )
    
    filtered_df = df[mask].copy()
    logger.info(f"Filtered {len(df)} records to {len(filtered_df)} ASTM D4541 records.")
    
    return filtered_df

def exclude_missing_target_records(df: pd.DataFrame, target_col: str = "adhesion_strength") -> pd.DataFrame:
    """Exclude records with missing target variables."""
    initial_count = len(df)
    df_clean = df.dropna(subset=[target_col])
    excluded_count = initial_count - len(df_clean)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records with missing target '{target_col}'.")
    return df_clean

def resolve_duplicates(df: pd.DataFrame, date_col: str = "date", sample_count_col: str = "sample_count") -> pd.DataFrame:
    """
    Resolve duplicates by keeping the most recent date or highest sample count.
    
    Logic:
    1. Identify duplicates based on a unique key (e.g., sample_id, coating_id).
    2. If duplicates exist, sort by date (desc) then sample_count (desc).
    3. Keep the first occurrence.
    """
    # Assuming 'sample_id' is the unique identifier for duplicates
    if 'sample_id' not in df.columns:
        logger.warning("No 'sample_id' column found. Skipping duplicate resolution.")
        return df
    
    initial_count = len(df)
    # Sort by date (descending) and sample_count (descending)
    # Handle potential NaT or missing values in date_col
    df_sorted = df.sort_values(
        by=[date_col, sample_count_col], 
        ascending=[False, False], 
        na_position='last'
    )
    
    # Drop duplicates keeping the first (which is now the best due to sort)
    df_deduped = df_sorted.drop_duplicates(subset=['sample_id'], keep='first')
    
    excluded_count = initial_count - len(df_deduped)
    if excluded_count > 0:
        logger.info(f"Resolved {excluded_count} duplicate records.")
    
    return df_deduped

def sample_dataset_to_memory_limit(df: pd.DataFrame, max_rows: int = 5000) -> pd.DataFrame:
    """Sample dataset to memory limit if raw volume exceeds it."""
    if len(df) > max_rows:
        logger.info(f"Dataset size ({len(df)}) exceeds limit ({max_rows}). Sampling.")
        return df.sample(n=max_rows, random_state=42)
    return df

def exclude_missing_surface_roughness(df: pd.DataFrame, roughness_col: str = "surface_roughness") -> pd.DataFrame:
    """Exclude records with missing surface roughness."""
    if roughness_col not in df.columns:
        logger.warning(f"Column '{roughness_col}' not found. Skipping exclusion.")
        return df
    
    initial_count = len(df)
    df_clean = df.dropna(subset=[roughness_col])
    excluded_count = initial_count - len(df_clean)
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records with missing surface roughness.")
    return df_clean

def align_records_strictly(df1: pd.DataFrame, df2: pd.DataFrame, key_col: str = "sample_id") -> pd.DataFrame:
    """
    Align records strictly using only unique, verified identifiers.
    
    Logic:
    1. Perform an inner join on the specified key column.
    2. Any record pair that cannot be linked is excluded.
    """
    if key_col not in df1.columns or key_col not in df2.columns:
        raise DataGapError(f"Key column '{key_col}' missing in one of the datasets.")
    
    merged_df = pd.merge(df1, df2, on=key_col, how='inner')
    logger.info(f"Aligned {len(merged_df)} records strictly on '{key_col}'.")
    return merged_df

def process_ingestion_data(data_source: str, config: Dict[str, Any]) -> pd.DataFrame:
    """Main ingestion processing logic."""
    logger.info(f"Processing ingestion for data source: {data_source}")
    
    if data_source == "materials_project":
        df = fetch_materials_project_data(
            api_key=config.get("MP_API_KEY"),
            endpoint=config.get("MP_URL")
        )
        # Convert to DataFrame if needed
        if isinstance(df, dict) and "results" in df:
            df = pd.DataFrame(df["results"])
        elif isinstance(df, list):
            df = pd.DataFrame(df)
    elif data_source == "nist":
        df = fetch_nist_surface_metrology_data(config.get("NIST_URL"))
        if isinstance(df, dict) and "data" in df:
            df = pd.DataFrame(df["data"])
        elif isinstance(df, list):
            df = pd.DataFrame(df)
    else:
        raise DataGapError(f"Unknown data source: {data_source}")
    
    return df

def main():
    """Main entry point for ingestion module."""
    logger.info("Ingestion module loaded.")
    # Example usage (would require real config and data)
    # df = pd.DataFrame({'test_method': ['ASTM D4541', 'ISO 4624', 'pull-off'], 'id': [1, 2, 3]})
    # filtered = filter_astm_d4541_records(df)
    # print(filtered)

if __name__ == "__main__":
    main()