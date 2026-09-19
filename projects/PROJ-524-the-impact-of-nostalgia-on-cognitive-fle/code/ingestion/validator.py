import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
from config import get_config, get_mmse_threshold

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataGapError(Exception):
    """Raised when expected data gaps are detected."""
    pass

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass

def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates that the dataframe contains required columns.
    
    Args:
        df: The dataframe to validate.
        
    Returns:
        Tuple of (is_valid, list of missing columns).
    """
    required_columns = ['age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Schema validation failed. Missing columns: {missing_columns}")
        return False, missing_columns
    
    logger.info("Schema validation passed.")
    return True, []

def validate_and_filter_dataset(df: pd.DataFrame, simulation_mode: bool = False) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Validates the dataset schema and applies initial filters:
    1. Filter age >= 65
    2. Exclude missing stimulus_type
    
    Args:
        df: Input dataframe.
        simulation_mode: If True, allows missing MMSE column without error.
        
    Returns:
        Tuple of (filtered dataframe, exclusion counts).
    """
    exclusion_counts = {}
    
    # Validate schema first
    is_valid, missing_cols = validate_schema(df)
    if not is_valid:
        raise SchemaValidationError(f"Schema validation failed. Missing columns: {missing_cols}")
    
    initial_count = len(df)
    
    # Filter 1: Age >= 65
    # Ensure age is numeric
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    age_missing = df['age'].isna().sum()
    if age_missing > 0:
        log_warning(f"Found {age_missing} rows with missing age values. Logging as ERR_MISSING_AGE_FIELD.")
    
    df_filtered_age = df.dropna(subset=['age'])
    df_filtered_age = df_filtered_age[df_filtered_age['age'] >= 65]
    
    excluded_age = initial_count - len(df_filtered_age)
    exclusion_counts['ERR_MISSING_AGE_FIELD'] = excluded_age
    log_info(f"Filtered {excluded_age} records for age < 65 or missing age. Remaining: {len(df_filtered_age)}")
    
    # Filter 2: Exclude missing stimulus_type
    # Ensure stimulus_type is string and not empty
    df_filtered_age['stimulus_type'] = df_filtered_age['stimulus_type'].astype(str)
    mask_stimulus = df_filtered_age['stimulus_type'].isin(['', 'nan', 'None', 'NaN']) | df_filtered_age['stimulus_type'].isna()
    
    excluded_stimulus = mask_stimulus.sum()
    if excluded_stimulus > 0:
        log_warning(f"Found {excluded_stimulus} records with missing/invalid stimulus_type.")
    
    df_clean = df_filtered_age[~mask_stimulus]
    exclusion_counts['ERR_MISSING_STIMULUS_TYPE'] = excluded_stimulus
    log_info(f"Filtered {excluded_stimulus} records with missing stimulus_type. Remaining: {len(df_clean)}")
    
    return df_clean, exclusion_counts

def clean_data(df: pd.DataFrame, simulation_mode: bool = False) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Main cleaning pipeline entry point.
    Applies age and stimulus_type filters.
    
    Args:
        df: Input dataframe.
        simulation_mode: Flag indicating if running in simulation mode.
        
    Returns:
        Tuple of (cleaned dataframe, exclusion counts).
    """
    return validate_and_filter_dataset(df, simulation_mode)

def save_exclusion_log(exclusion_counts: Dict[str, int], path: str) -> None:
    """
    Saves exclusion counts to a JSON file.
    
    Args:
        exclusion_counts: Dictionary of exclusion reasons and counts.
        path: Output file path.
    """
    # Load existing log if it exists to append/merge
    existing_log = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                existing_log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_warning(f"Could not read existing exclusion log at {path}. Overwriting.")
    
    # Merge counts
    for key, count in exclusion_counts.items():
        existing_log[key] = existing_log.get(key, 0) + count
    
    with open(path, 'w') as f:
        json.dump(existing_log, f, indent=2)
    log_info(f"Exclusion log saved to {path}")

def calculate_validity_metrics(raw_count: int, valid_count: int) -> Dict[str, Any]:
    """
    Calculates validity metrics.
    
    Args:
        raw_count: Total raw records.
        valid_count: Total valid records after cleaning.
        
    Returns:
        Dictionary with validity metrics.
    """
    if raw_count == 0:
        validity_percentage = 0.0
    else:
        validity_percentage = (valid_count / raw_count) * 100
    
    return {
        "total_raw_records": raw_count,
        "total_valid_records": valid_count,
        "validity_percentage": validity_percentage,
        "target_met": validity_percentage >= 90.0
    }

def save_validity_metrics(metrics: Dict[str, Any], path: str) -> None:
    """
    Saves validity metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics.
        path: Output file path.
    """
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info(f"Validity metrics saved to {path}")