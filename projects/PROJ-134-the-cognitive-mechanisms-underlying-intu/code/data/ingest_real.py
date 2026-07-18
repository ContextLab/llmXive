import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PROJECT_ROOT, get_path

# Setup logging
logger = logging.getLogger(__name__)

# ============================================================================
# REAL DATA ARCHITECTURE CONSTANTS (Defined in T050)
# ============================================================================

# OSF API Base URL
OSF_API_URL = "https://api.osf.io/v2"

# HuggingFace Dataset ID for Moral Stories (Example: "moral_stories_v1")
# In a real implementation, this would be a verified dataset ID
HF_DATASET_ID = "moral-judgments/moral_stories_v1"

# VR Log Schema Columns (Required fields)
VR_LOG_SCHEMA_COLUMNS = [
    "response_time",
    "gaze_x",
    "gaze_y",
    "judgment_rating"
]

# ============================================================================
# Custom Exceptions
# ============================================================================

class DataFetchError(Exception):
    """Raised when real data fetch fails."""
    pass

class SchemaError(Exception):
    """Raised when data schema validation fails."""
    pass

# ============================================================================
# Real Data Fetchers
# ============================================================================

def fetch_real_mfq_data() -> pd.DataFrame:
    """
    Fetch real MFQ data from OSF.
    
    Returns:
        DataFrame with MFQ data
    
    Raises:
        DataFetchError: If fetch fails
    """
    logger.info(f"Attempting to fetch MFQ data from OSF: {OSF_API_URL}")
    
    # NOTE: In a real implementation, this would make an actual API call.
    # For this simulation of the 'real' mode (since we cannot guarantee 
    # network access or valid credentials in this environment), we raise
    # a clear error if the expected data file is not present locally.
    # This satisfies the "Fail Loudly" requirement without fabricating data.
    
    # Check for a pre-downloaded real dataset (simulating a successful fetch)
    local_path = get_path("data/raw/osf_mfq_data.csv")
    if not local_path.exists():
        raise DataFetchError(
            f"Real data fetch failed: Expected file {local_path} not found. "
            "In a real environment, this would attempt to download from {OSF_API_URL}. "
            "Please ensure real data is available or run in simulation mode."
        )
    
    try:
        df = pd.read_csv(local_path)
        # Validate schema
        if 'participant_id' not in df.columns or 'foundation_score' not in df.columns:
            raise SchemaError("Downloaded MFQ data missing required columns")
        return df
    except Exception as e:
        raise DataFetchError(f"Failed to parse real MFQ data: {e}")

def fetch_real_stories_data() -> pd.DataFrame:
    """
    Fetch real Moral Stories data from HuggingFace.
    
    Returns:
        DataFrame with Moral Stories data
    
    Raises:
        DataFetchError: If fetch fails
    """
    logger.info(f"Attempting to fetch Moral Stories from HuggingFace: {HF_DATASET_ID}")
    
    local_path = get_path("data/raw/hf_moral_stories.csv")
    if not local_path.exists():
        raise DataFetchError(
            f"Real data fetch failed: Expected file {local_path} not found. "
            "In a real environment, this would download from HF dataset {HF_DATASET_ID}. "
            "Please ensure real data is available or run in simulation mode."
        )
    
    try:
        df = pd.read_csv(local_path)
        if 'story_id' not in df.columns or 'story_text' not in df.columns:
            raise SchemaError("Downloaded Stories data missing required columns")
        return df
    except Exception as e:
        raise DataFetchError(f"Failed to parse real Moral Stories data: {e}")

def fetch_real_vr_logs() -> pd.DataFrame:
    """
    Fetch real VR interaction logs.
    
    Returns:
        DataFrame with VR logs
    
    Raises:
        DataFetchError: If fetch fails
    """
    logger.info("Attempting to fetch real VR logs...")
    
    local_path = get_path("data/raw/vr_interaction_logs.csv")
    if not local_path.exists():
        raise DataFetchError(
            f"Real data fetch failed: Expected file {local_path} not found. "
            "Please ensure real data is available or run in simulation mode."
        )
    
    try:
        df = pd.read_csv(local_path)
        # Validate schema against T050 definition
        missing_cols = [col for col in VR_LOG_SCHEMA_COLUMNS if col not in df.columns]
        if missing_cols:
            raise SchemaError(f"VR logs missing required schema columns: {missing_cols}")
        return df
    except Exception as e:
        raise DataFetchError(f"Failed to parse real VR logs: {e}")

def validate_real_data_schema(data: pd.DataFrame, expected_columns: List[str]) -> None:
    """
    Validate that a DataFrame matches the expected schema.
    
    Args:
        data: DataFrame to validate
        expected_columns: List of required column names
    
    Raises:
        SchemaError: If validation fails
    """
    missing = [col for col in expected_columns if col not in data.columns]
    if missing:
        raise SchemaError(f"Data missing required columns: {missing}")

def parse_vr_logs_from_csv(file_path: str) -> pd.DataFrame:
    """
    Parse VR logs from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        DataFrame with parsed VR logs
    
    Raises:
        SchemaError: If schema validation fails
    """
    df = pd.read_csv(file_path)
    validate_real_data_schema(df, VR_LOG_SCHEMA_COLUMNS)
    return df

def parse_vr_logs_from_json(file_path: str) -> pd.DataFrame:
    """
    Parse VR logs from a JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        DataFrame with parsed VR logs
    
    Raises:
        SchemaError: If schema validation fails
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    validate_real_data_schema(df, VR_LOG_SCHEMA_COLUMNS)
    return df

def main():
    """Main entry point for real data ingestion (testing)."""
    logger.info("Testing real data ingestion interface...")
    try:
        # This will fail loudly if real data is not present
        _ = fetch_real_mfq_data()
        _ = fetch_real_stories_data()
        _ = fetch_real_vr_logs()
        logger.info("All real data sources accessible.")
    except DataFetchError as e:
        logger.error(f"DataFetchError: {e}")
        # Re-raise to ensure the pipeline halts
        raise

if __name__ == "__main__":
    main()