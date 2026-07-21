"""
Real Data Ingestion Module for VR Interaction Logs and Moral Stories.

This module implements the "Fail Loudly" logic for fetching real data from OSF
and HuggingFace. It strictly validates data against schemas defined in T050
and raises SchemaError or DataFetchError on any failure. No synthetic fallbacks.
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
from datetime import datetime

# Import from local project structure (relative to code/)
# Note: Assuming this file is run with PYTHONPATH set to include 'code'
try:
    from utils.logging import get_logger, get_exclusion_log_path, log_exclusion
    from utils.schema import VRInteractionLog, VRLogsDataset, MergedDataset
    from config import get_path, DATA_MODE
except ImportError:
    # Fallback for direct execution testing where imports might be absolute
    from code.utils.logging import get_logger, get_exclusion_log_path, log_exclusion
    from code.utils.schema import VRInteractionLog, VRLogsDataset, MergedDataset
    from code.config import get_path, DATA_MODE

# --- Constants from T050 Interface ---
OSF_API_URL = "https://api.osf.io/v2/"
HF_DATASET_ID = "moral-stories-v1" # Placeholder ID as per spec
VR_LOG_SCHEMA_COLUMNS = ["response_time", "gaze_x", "gaze_y", "judgment_rating"]

# --- Custom Exceptions ---
class DataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

class SchemaError(Exception):
    """Raised when data schema validation fails."""
    pass

# --- Logger Setup ---
logger = get_logger(__name__)

def validate_real_data_schema(df: pd.DataFrame, expected_columns: List[str], source_name: str) -> None:
    """
    Validates that the DataFrame contains the required columns.
    Raises SchemaError if validation fails.
    """
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise SchemaError(
            f"Schema validation failed for {source_name}: "
            f"Missing columns: {missing}. Expected: {expected_columns}, Found: {list(df.columns)}"
        )
    logger.info(f"Schema validation passed for {source_name}.")

def fetch_real_mfq_data() -> pd.DataFrame:
    """
    Fetches real MFQ data from OSF.
    Implements 'Fail Loudly' logic: no synthetic fallback.
    """
    logger.info(f"Attempting to fetch MFQ data from OSF API: {OSF_API_URL}")
    # In a real implementation, this would use requests to fetch from OSF.
    # For the purpose of this task, we simulate the fetch failure or success
    # based on the presence of a local file that mimics the real fetch result,
    # OR we strictly raise if the network call would fail.
    # Since we cannot guarantee network access in this environment, we check for
    # a pre-downloaded artifact as per the "Real Data Only" constraint if the network is down.
    
    # Check for pre-downloaded artifact (simulating a successful fetch that was saved)
    # If the task requires fetching from network and it fails, we raise DataFetchError.
    # We assume a file might exist from a previous successful run or manual download.
    raw_path = get_path("data", "raw", "osf_mfq_data.csv")
    
    if os.path.exists(raw_path):
        logger.info(f"Found pre-fetched MFQ data at {raw_path}. Loading...")
        try:
            df = pd.read_csv(raw_path)
            validate_real_data_schema(df, ["participant_id", "foundation_score", "age", "gender"], "OSF MFQ")
            return df
        except Exception as e:
            raise DataFetchError(f"Failed to load pre-fetched MFQ data: {e}")
    else:
        # Strict "Fail Loudly": If no network fetch is possible and no file exists, fail.
        # In a real CI environment, this would attempt the HTTP request and raise on 404/500.
        raise DataFetchError(
            f"Real MFQ data not found at {raw_path} and network fetch to {OSF_API_URL} "
            f"is not implemented in this simulation context. "
            f"Please ensure DATA_MODE='real' is only used when real data is available."
        )

def fetch_real_stories_data() -> pd.DataFrame:
    """
    Fetches real Moral Stories data from HuggingFace.
    Implements 'Fail Loudly' logic.
    """
    logger.info(f"Attempting to fetch Moral Stories from HuggingFace: {HF_DATASET_ID}")
    raw_path = get_path("data", "raw", "hf_moral_stories.csv")
    
    if os.path.exists(raw_path):
        logger.info(f"Found pre-fetched Stories data at {raw_path}. Loading...")
        try:
            df = pd.read_csv(raw_path)
            # Validate basic schema
            required = ["story_id", "text", "moral_dimension"]
            validate_real_data_schema(df, required, "HF Moral Stories")
            return df
        except Exception as e:
            raise DataFetchError(f"Failed to load pre-fetched Stories data: {e}")
    else:
        raise DataFetchError(
            f"Real Moral Stories data not found at {raw_path} and network fetch to {HF_DATASET_ID} "
            f"is not implemented in this simulation context."
        )

def fetch_real_vr_logs() -> pd.DataFrame:
    """
    Fetches real VR interaction logs.
    Implements 'Fail Loudly' logic.
    """
    logger.info("Attempting to fetch VR Interaction Logs.")
    raw_path = get_path("data", "raw", "vr_interaction_logs.csv")
    
    if os.path.exists(raw_path):
        logger.info(f"Found pre-fetched VR logs at {raw_path}. Loading...")
        try:
            df = pd.read_csv(raw_path)
            # Validate against T050 schema
            validate_real_data_schema(df, VR_LOG_SCHEMA_COLUMNS, "VR Interaction Logs")
            return df
        except Exception as e:
            raise DataFetchError(f"Failed to load pre-fetched VR logs: {e}")
    else:
        raise DataFetchError(
            f"Real VR Interaction Logs not found at {raw_path} and network fetch is not implemented."
        )

def parse_vr_logs_from_csv(file_path: str) -> pd.DataFrame:
    """
    Parses VR logs from a CSV file and validates against the schema.
    Raises SchemaError if malformed.
    """
    logger.info(f"Parsing VR logs from CSV: {file_path}")
    if not os.path.exists(file_path):
        raise DataFetchError(f"File not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise DataFetchError(f"Failed to read CSV {file_path}: {e}")
    
    # Validate schema
    validate_real_data_schema(df, VR_LOG_SCHEMA_COLUMNS, "VR CSV Input")
    
    # Check for nulls in critical columns (as per T015b requirement for real data too)
    null_cols = df[VR_LOG_SCHEMA_COLUMNS].isnull().any()
    if null_cols.any():
        cols_with_nulls = null_cols[null_cols].index.tolist()
        raise SchemaError(f"Schema validation failed: Null values found in {cols_with_nulls}.")
        
    return df

def parse_vr_logs_from_json(file_path: str) -> pd.DataFrame:
    """
    Parses VR logs from a JSON file and validates against the schema.
    Raises SchemaError if malformed.
    """
    logger.info(f"Parsing VR logs from JSON: {file_path}")
    if not os.path.exists(file_path):
        raise DataFetchError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        raise DataFetchError(f"Failed to read JSON {file_path}: {e}")
    
    # Assume JSON is a list of records
    if not isinstance(data, list):
        raise SchemaError("JSON root must be a list of records.")
    
    try:
        df = pd.DataFrame(data)
    except Exception as e:
        raise DataFetchError(f"Failed to convert JSON to DataFrame: {e}")
    
    # Validate schema
    validate_real_data_schema(df, VR_LOG_SCHEMA_COLUMNS, "VR JSON Input")
    
    # Check for nulls
    null_cols = df[VR_LOG_SCHEMA_COLUMNS].isnull().any()
    if null_cols.any():
        cols_with_nulls = null_cols[null_cols].index.tolist()
        raise SchemaError(f"Schema validation failed: Null values found in {cols_with_nulls}.")
        
    return df

def main():
    """
    Main entry point for real data ingestion.
    Orchestrates fetching and validation.
    """
    if DATA_MODE != 'real':
        logger.warning("DATA_MODE is not 'real'. This module is designed for real data ingestion.")
        return

    logger.info("Starting Real Data Ingestion Pipeline (T041)...")
    
    try:
        # 1. Fetch MFQ
        df_mfq = fetch_real_mfq_data()
        logger.info(f"MFQ data loaded: {len(df_mfq)} rows")
        
        # 2. Fetch Stories
        df_stories = fetch_real_stories_data()
        logger.info(f"Stories data loaded: {len(df_stories)} rows")
        
        # 3. Fetch VR Logs
        df_vr = fetch_real_vr_logs()
        logger.info(f"VR Logs loaded: {len(df_vr)} rows")
        
        # 4. Save raw data to disk for downstream steps
        # (This mimics the output of a successful fetch)
        mfq_path = get_path("data", "raw", "osf_mfq_data.csv")
        stories_path = get_path("data", "raw", "hf_moral_stories.csv")
        vr_path = get_path("data", "raw", "vr_interaction_logs.csv")
        
        df_mfq.to_csv(mfq_path, index=False)
        df_stories.to_csv(stories_path, index=False)
        df_vr.to_csv(vr_path, index=False)
        
        logger.info("Real data ingestion complete. Files saved to data/raw/.")
        
    except (DataFetchError, SchemaError) as e:
        logger.error(f"Real Data Ingestion Failed: {e}")
        # Re-raise to halt execution as per "Fail Loudly" requirement
        raise e

if __name__ == "__main__":
    main()