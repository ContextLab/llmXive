import os
import sys
import json
import hashlib
import logging
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('data/ingestion.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants for critical variables
CRITICAL_COLUMNS = {
    'rolling_temperature', 'temperature', 'temp',  # Variants for temperature
    'grain_size', 'grain_size_um', 'grain_diameter' # Variants for grain size
}
COMPOSITION_COLUMNS = {
    'mg', 'magnesium', 'si', 'silicon', 'cu', 'copper', 
    'al', 'aluminum', 'zn', 'zinc', 'mn', 'manganese'
}

def fetch_sources() -> List[Dict[str, Any]]:
    """
    Fetches data from configured public sources (OpenML, NOMAD, Citrination).
    Returns a list of DataFrames or raw data dictionaries.
    """
    sources_data = []
    logger.info("Starting data fetch from configured sources...")
    
    # Placeholder for actual fetching logic implemented in T013
    # In a real scenario, this would call specific API clients or downloaders
    # For this implementation, we assume T013 has populated data/processed/raw_sources.json
    # or similar, or we fetch live here.
    
    # Attempt to load from a previously downloaded state if available (T013 output)
    raw_data_path = "data/raw/sources_combined.json"
    if os.path.exists(raw_data_path):
        logger.info(f"Loading pre-fetched data from {raw_data_path}")
        with open(raw_data_path, 'r') as f:
            sources_data = json.load(f)
    else:
        logger.warning(f"No pre-fetched data found at {raw_data_path}. Attempting live fetch.")
        # Simulate fetching logic that would be in T013
        # In a real run, this block would contain the actual HTTP requests
        # For the purpose of this task implementation, we assume the fetch function
        # from T013 populates this or we raise an error if not found.
        # Since T013 is "download and parsing", we assume it writes to data/raw/
        # If that file doesn't exist, we cannot proceed with filtering real data.
        # We will attempt to simulate the structure expected if T013 ran successfully.
        # However, per strict constraints, we must use REAL data.
        # If the file is missing, we assume T013 failed or wasn't run.
        # We will raise an error to indicate T014 cannot run without T013 output.
        raise FileNotFoundError(
            "Required raw data file 'data/raw/sources_combined.json' not found. "
            "Please ensure T013 (download and parsing) has been executed successfully."
        )

    return sources_data

def check_schema(data: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Checks if critical variables exist in the fetched data.
    Returns a list of missing variables and a dict of source -> missing fields.
    """
    all_missing_vars = set()
    source_missing_map = {}

    for source_idx, source_data in enumerate(data):
        if isinstance(source_data, dict) and 'columns' in source_data:
            columns = source_data['columns']
        elif isinstance(source_data, pd.DataFrame):
            columns = list(source_data.columns)
        else:
            # Fallback for raw dict structures
            if isinstance(source_data, dict):
                columns = list(source_data.keys())
            else:
                columns = []

        missing_in_source = []
        # Check for temperature variants
        temp_found = any(col.lower() in [c.lower() for c in columns] for col in ['rolling_temperature', 'temperature', 'temp'])
        if not temp_found:
            missing_in_source.append('rolling_temperature')
            all_missing_vars.add('rolling_temperature')

        # Check for grain size variants
        grain_found = any(col.lower() in [c.lower() for c in columns] for col in ['grain_size', 'grain_size_um', 'grain_diameter'])
        if not grain_found:
            missing_in_source.append('grain_size')
            all_missing_vars.add('grain_size')

        # Check for at least one composition element
        comp_found = any(col.lower() in [c.lower() for c in columns] for col in COMPOSITION_COLUMNS)
        if not comp_found:
            missing_in_source.append('composition')
            all_missing_vars.add('composition')

        if missing_in_source:
            source_missing_map[f"source_{source_idx}"] = missing_in_source

    return list(all_missing_vars), source_missing_map

def filter_data(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Filters and validates the combined dataset.
    - Excludes rows with null critical variables (temperature, grain_size, composition).
    - Reports final dataset size.
    - Returns a clean DataFrame.
    """
    if not data:
        logger.error("No data provided to filter_data.")
        return pd.DataFrame()

    # Combine all sources into a single DataFrame
    # Assuming data is a list of dicts or DataFrames
    dfs = []
    for i, item in enumerate(data):
        if isinstance(item, pd.DataFrame):
            dfs.append(item)
        elif isinstance(item, dict) and 'data' in item:
            # Handle structured JSON from T013
            df = pd.DataFrame(item['data'])
            dfs.append(df)
        else:
            logger.warning(f"Skipping unsupported data format at index {i}")

    if not dfs:
        logger.error("No valid DataFrames found in input data.")
        return pd.DataFrame()

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset shape before filtering: {combined_df.shape}")

    # Normalize column names to lowercase for consistent checking
    combined_df.columns = combined_df.columns.str.lower()

    # Identify canonical column names for critical variables
    temp_col = None
    grain_col = None
    comp_cols = []

    for col in combined_df.columns:
        if any(t in col for t in ['rolling_temperature', 'temperature', 'temp']):
            temp_col = col
        elif any(g in col for g in ['grain_size', 'grain_size_um', 'grain_diameter']):
            grain_col = col
        elif any(c in col for c in COMPOSITION_COLUMNS):
            comp_cols.append(col)

    if not temp_col:
        raise ValueError("Temperature column not found in combined data.")
    if not grain_col:
        raise ValueError("Grain size column not found in combined data.")
    if not comp_cols:
        raise ValueError("No composition columns found in combined data.")

    # Ensure critical columns exist in the dataframe
    # (They should, based on schema check, but good to be safe)
    assert temp_col in combined_df.columns
    assert grain_col in combined_df.columns

    # Filter out rows with null values in critical columns
    initial_count = len(combined_df)
    
    # Create a mask for valid rows
    valid_mask = combined_df[temp_col].notna() & combined_df[grain_col].notna()
    
    # Also check composition: at least one composition column must be non-null
    if comp_cols:
        comp_mask = combined_df[comp_cols].notna().any(axis=1)
        valid_mask = valid_mask & comp_mask

    filtered_df = combined_df[valid_mask].reset_index(drop=True)
    final_count = len(filtered_df)

    dropped_count = initial_count - final_count
    drop_pct = (dropped_count / initial_count * 100) if initial_count > 0 else 0

    logger.info(f"Filtering complete.")
    logger.info(f"Initial rows: {initial_count}")
    logger.info(f"Dropped rows (null critical vars): {dropped_count} ({drop_pct:.2f}%)")
    logger.info(f"Final dataset size: {final_count} rows")

    if final_count == 0:
        logger.error("CRITICAL: All rows were filtered out. No valid data remains.")
        # This will likely trigger the halt logic in T015
        return filtered_df

    return filtered_df

def generate_checksum(df: pd.DataFrame, output_path: str) -> str:
    """
    Generates a SHA-256 checksum for the processed DataFrame.
    Saves the DataFrame to CSV and returns the checksum string.
    """
    if df.empty:
        logger.warning("DataFrame is empty, generating checksum for empty file.")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")

    # Calculate checksum
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()
    logger.info(f"Generated SHA-256 checksum: {checksum}")
    return checksum

def run_pipeline() -> bool:
    """
    Orchestrates the full ingestion pipeline:
    1. Fetch sources (T013 logic assumed done)
    2. Check schema (T012 logic)
    3. Filter data (T014 logic - THIS TASK)
    4. Generate checksum (T016 logic)
    
    Returns True if successful, False otherwise.
    """
    try:
        # 1. Fetch
        sources = fetch_sources()
        if not sources:
            logger.error("No sources fetched.")
            return False

        # 2. Check Schema
        missing_vars, source_map = check_schema(sources)
        if missing_vars:
            logger.warning(f"Missing variables detected in some sources: {missing_vars}")
            # Note: T015 handles the hard halt if ALL sources are missing critical vars.
            # We continue here to see if any valid data exists.

        # 3. Filter Data (T014 Core Logic)
        clean_df = filter_data(sources)

        if clean_df.empty:
            logger.error("Filtered dataset is empty. Pipeline cannot proceed.")
            return False

        # 4. Generate Checksum and Save
        output_path = "data/processed/filtered_aluminum_data.csv"
        checksum = generate_checksum(clean_df, output_path)

        # Log final status
        logger.info(f"Pipeline completed successfully. Output: {output_path}")
        logger.info(f"Checksum: {checksum}")
        
        return True

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
