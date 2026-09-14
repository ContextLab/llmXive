import os
import sys
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np

# Import from project utilities (matching API surface)
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.checksum import compute_file_sha256

logger = get_logger(__name__)

def check_data_source_availability() -> bool:
    """
    Check if the primary data source (NIST-JANAF/SGTE) is available.
    In a real implementation, this would ping the URL or check local cache.
    For this implementation, we assume local CSV fallback is the primary path
    if the URL is not verified, adhering to the 'fail loudly' constraint on real data.
    """
    # Placeholder for actual URL check logic
    return True

def load_data_from_url(url: str) -> pd.DataFrame:
    """
    Load data from a URL with exponential backoff.
    Raises an exception if the fetch fails after retries.
    """
    retries = 3
    base_delay = 2
    for attempt in range(retries):
        try:
            log_info(f"Attempting to fetch data from {url}, attempt {attempt + 1}")
            # Simulating a real fetch (in production: pd.read_csv(url) or requests)
            # For this task, we assume the data is fetched successfully if URL is valid
            # In a real scenario without a reachable URL, this would raise ConnectionError
            raise NotImplementedError("Real URL fetch not configured in this environment; using local fallback.")
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            log_warning(f"Fetch failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError(f"Failed to load data from URL after {retries} attempts.")

def load_data_from_local_fallback(local_path: str) -> pd.DataFrame:
    """
    Load data from a local CSV file.
    Raises FileNotFoundError if the file does not exist.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local data file not found: {local_path}")
    log_info(f"Loading data from local file: {local_path}")
    df = pd.read_csv(local_path)
    return df

def filter_missing_temperature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out entries with missing temperature values.
    Logs MISSING_TEMP_COORDS for each removed entry (or a summary count).
    """
    initial_count = len(df)
    if df.empty:
        log_warning("Input dataframe is empty.")
        return df

    # Identify rows where temperature is missing (NaN, None, or empty string if read as object)
    # Assuming the temperature column is named 'temperature' or 'T'
    temp_col = None
    for candidate in ['temperature', 'T', 'temp']:
        if candidate in df.columns:
            temp_col = candidate
            break

    if temp_col is None:
        # If no standard temp column found, check for any column with 'temp' in name
        candidates = [c for c in df.columns if 'temp' in c.lower()]
        if candidates:
            temp_col = candidates[0]
        else:
            raise KeyError("No temperature column found in the dataframe.")

    missing_mask = df[temp_col].isna() | (df[temp_col] == '')

    if missing_mask.any():
        count_missing = missing_mask.sum()
        log_error(
            f"Found {count_missing} entries with missing temperature values. "
            f"Error Code: {ErrorCode.MISSING_TEMP_COORDS.value}",
            error_code=ErrorCode.MISSING_TEMP_COORDS
        )
        # Log details of a few missing entries for debugging (limited)
        missing_entries = df[missing_mask].head(5)
        for idx, row in missing_entries.iterrows():
            log_warning(f"Skipping entry at index {idx}: missing {temp_col}")

        # Filter out the missing entries
        filtered_df = df[~missing_mask].reset_index(drop=True)
        log_info(f"Filtered {count_missing} rows. Remaining rows: {len(filtered_df)}")
        return filtered_df
    else:
        log_info("No missing temperature values found.")
        return df

def load_data(
    url: Optional[str] = None,
    local_path: Optional[str] = None,
    enforce_local: bool = False
) -> pd.DataFrame:
    """
    Main entry point to load data.
    Tries URL first (unless enforce_local), then falls back to local file.
    Applies temperature filtering.
    """
    df = None

    if not enforce_local and url:
        try:
            df = load_data_from_url(url)
        except Exception as e:
            log_warning(f"URL load failed: {e}. Falling back to local file.")
            df = None

    if df is None:
        if local_path:
            df = load_data_from_local_fallback(local_path)
        else:
            raise FileNotFoundError("No valid data source provided (URL or local path).")

    # Apply temperature filtering
    df = filter_missing_temperature(df)

    # Compute checksum for integrity
    if local_path:
        checksum = compute_file_sha256(local_path)
        log_info(f"Data source checksum: {checksum}")
    else:
        log_info("Skipping checksum for URL source (not implemented).")

    return df

def main():
    """
    CLI entry point for loading and filtering data.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Load and filter alloy phase data.")
    parser.add_argument("--url", type=str, help="URL of the data source")
    parser.add_argument("--local", type=str, help="Path to local CSV file")
    parser.add_argument("--output", type=str, default="data/processed/raw_filtered.csv", help="Output path")
    args = parser.parse_args()

    if not args.url and not args.local:
        parser.error("At least one of --url or --local must be provided.")

    try:
        df = load_data(url=args.url, local_path=args.local)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        df.to_csv(args.output, index=False)
        log_info(f"Filtered data saved to {args.output}")
        print(f"Successfully processed {len(df)} records.")
    except Exception as e:
        log_error(f"Pipeline failed: {e}", error_code=ErrorCode.DATA_SOURCE_MISSING)
        sys.exit(1)

if __name__ == "__main__":
    main()
