import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd

from utils import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Exception raised when data fetching fails."""
    pass

class DataGapError(Exception):
    """Exception raised when a required data gap is detected."""
    pass

class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validates the DataFrame against a schema.
    
    Args:
        df: DataFrame to validate.
        schema_path: Path to the schema file.
    
    Returns:
        True if valid.
    
    Raises:
        SchemaValidationError: If validation fails.
    """
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        required_cols = schema.get('required_columns', [])
        for col in required_cols:
            if col not in df.columns:
                raise SchemaValidationError(f"Missing required column: {col}")
        
        log_info("Schema validation passed.")
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise SchemaValidationError(f"Schema validation failed: {e}")

def validate_and_filter_dataset(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Validates and filters the dataset based on config.
    
    Args:
        df: DataFrame to process.
        config: Configuration dictionary.
    
    Returns:
        Filtered DataFrame.
    """
    # Basic validation
    if 'age' in df.columns:
        df = df[df['age'] >= config.get('min_age', 0)]
    
    if 'stimulus_type' in df.columns:
        df = df.dropna(subset=['stimulus_type'])
    
    return df

def clean_data(df: pd.DataFrame, simulation_mode: bool) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Cleans the dataset and returns exclusion counts.
    
    Args:
        df: Input DataFrame.
        simulation_mode: Whether the data is simulated.
    
    Returns:
        Tuple of (Cleaned DataFrame, Exclusion counts).
    """
    exclusion_counts = {
        "ERR_MISSING_AGE_FIELD": 0,
        "ERR_MISSING_SCORE": 0,
        "ERR_MMSE_IMPAIRED": 0,
        "SIMULATION_FALLBACK": 1 if simulation_mode else 0
    }
    
    # Filter for non-null scores
    initial_count = len(df)
    
    if 'perseverative_errors' in df.columns and 'categories_completed' in df.columns:
        df = df.dropna(subset=['perseverative_errors', 'categories_completed'])
        excluded = initial_count - len(df)
        if excluded > 0:
            exclusion_counts["ERR_MISSING_SCORE"] = excluded
    else:
        log_warning("Score columns missing, skipping score exclusion.")
    
    # Handle MMSE if present
    if 'MMSE' in df.columns:
        mmse_count = df['MMSE'].notna().sum()
        if mmse_count > 0:
            # Filter MMSE >= 24
            mmse_filtered = df[df['MMSE'] >= 24]
            excluded = len(df) - len(mmse_filtered)
            if excluded > 0:
                exclusion_counts["ERR_MMSE_IMPAIRED"] = excluded
                df = mmse_filtered
            else:
                # Save robustness dataset (no MMSE filter)
                pass
        else:
            log_info("No MMSE data found.")
    else:
        log_info("MMSE column not present.")
    
    return df, exclusion_counts

def save_exclusion_log(exclusion_counts: Dict[str, int], filepath: str) -> None:
    """
    Saves exclusion log to a JSON file.
    
    Args:
        exclusion_counts: Dictionary of exclusion counts.
        filepath: Path to save the file.
    """
    with open(filepath, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    log_info(f"Exclusion log saved to {filepath}")

def calculate_validity_metrics(raw_count: int, valid_count: int) -> Dict[str, Any]:
    """
    Calculates validity metrics.
    
    Args:
        raw_count: Total raw records.
        valid_count: Total valid records.
    
    Returns:
        Dictionary with metrics.
    """
    validity_pct = (valid_count / raw_count * 100) if raw_count > 0 else 0.0
    return {
        "raw_count": raw_count,
        "valid_count": valid_count,
        "validity_percentage": validity_pct
    }

def save_validity_metrics(metrics: Dict[str, Any], filepath: str) -> None:
    """
    Saves validity metrics to a JSON file.
    
    Args:
        metrics: Dictionary with metrics.
        filepath: Path to save the file.
    """
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info(f"Validity metrics saved to {filepath}")
