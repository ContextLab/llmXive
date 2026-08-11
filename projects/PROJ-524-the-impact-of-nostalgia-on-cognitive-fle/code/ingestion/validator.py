import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import numpy as np

from utils import setup_logging, log_info, log_warning, log_error
from config import get_config, get_mmse_threshold

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    pass

class DataGapError(Exception):
    pass

class SchemaValidationError(Exception):
    pass

REQUIRED_COLUMNS = ['age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
OPTIONAL_COLUMNS = ['MMSE', 'participant_id']

def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that the dataframe contains required columns.
    
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    
    if missing:
        log_error(f"Schema validation failed. Missing columns: {missing}")
        return False, missing
    
    log_info("Schema validation passed.")
    return True, []

def validate_and_filter_dataset(df: pd.DataFrame, simulation_mode: bool) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Validate data and apply filtering rules.
    
    Args:
        df: Input dataframe.
        simulation_mode: If True, log SIMULATION_FALLBACK but don't fail.
        
    Returns:
        Tuple of (filtered_df, exclusion_counts)
    """
    exclusion_counts = {}
    
    # Check for age field
    if 'age' not in df.columns:
        exclusion_counts['ERR_MISSING_AGE_FIELD'] = len(df)
        log_error("ERR_MISSING_AGE_FIELD: 'age' column missing from dataset.")
        return pd.DataFrame(), exclusion_counts
    
    # Filter age >= 65
    total_before = len(df)
    df_valid_age = df[df['age'] >= 65].copy()
    excluded_age = total_before - len(df_valid_age)
    exclusion_counts['ERR_MISSING_AGE_FIELD'] = excluded_age
    log_info(f"Excluded {excluded_age} records with age < 65.")
    
    # Filter missing stimulus_type
    total_before = len(df_valid_age)
    df_valid_stim = df_valid_age.dropna(subset=['stimulus_type']).copy()
    excluded_stim = total_before - len(df_valid_stim)
    exclusion_counts['ERR_MISSING_STIMULUS_TYPE'] = excluded_stim
    log_info(f"Excluded {excluded_stim} records with missing stimulus_type.")
    
    # Filter missing scores
    total_before = len(df_valid_stim)
    df_valid_scores = df_valid_stim.dropna(subset=['perseverative_errors', 'categories_completed']).copy()
    excluded_scores = total_before - len(df_valid_scores)
    exclusion_counts['ERR_MISSING_SCORE'] = excluded_scores
    log_info(f"Excluded {excluded_scores} records with missing cognitive scores.")
    
    # Handle MMSE if present
    mmse_flag = False
    if 'MMSE' in df_valid_scores.columns:
        mmse_flag = True
        total_before = len(df_valid_scores)
        df_valid_mmse = df_valid_scores[df_valid_scores['MMSE'] >= 24].copy()
        excluded_mmse = total_before - len(df_valid_mmse)
        exclusion_counts['ERR_MMSE_IMPAIRED'] = excluded_mmse
        log_info(f"Excluded {excluded_mmse} records with MMSE < 24.")
        df_valid_scores = df_valid_mmse
    else:
        exclusion_counts['ERR_MMSE_IMPAIRED'] = 0
        log_info("MMSE column not present. Skipping MMSE exclusion.")
    
    if simulation_mode:
        exclusion_counts['SIMULATION_FALLBACK'] = 1
        log_warning("SIMULATION_FALLBACK: Using synthetic data for pipeline validation.")
    
    return df_valid_scores, exclusion_counts

def save_exclusion_log(exclusion_counts: Dict[str, int], path: str) -> None:
    """Save exclusion log to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    log_info(f"Exclusion log saved to {path}")

def clean_data(df: pd.DataFrame, simulation_mode: bool) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Main cleaning pipeline.
    
    Returns:
        Tuple of (cleaned_df, exclusion_counts)
    """
    # Validate schema
    is_valid, missing = validate_schema(df)
    if not is_valid:
        raise SchemaValidationError(f"Schema validation failed. Missing: {missing}")
    
    # Filter and validate
    cleaned_df, counts = validate_and_filter_dataset(df, simulation_mode)
    
    return cleaned_df, counts

def calculate_validity_metrics(raw_count: int, valid_count: int) -> Dict[str, Any]:
    """Calculate validity metrics."""
    if raw_count == 0:
        return {"validity_percentage": 0.0, "raw_count": 0, "valid_count": 0}
    
    percentage = (valid_count / raw_count) * 100
    return {
        "validity_percentage": round(percentage, 2),
        "raw_count": raw_count,
        "valid_count": valid_count,
        "excluded_count": raw_count - valid_count
    }

def save_validity_metrics(metrics: Dict[str, Any], path: str) -> None:
    """Save validity metrics to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info(f"Validity metrics saved to {path}")