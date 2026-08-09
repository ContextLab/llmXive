"""
Schema Validation Module for Nostalgia-Cognitive Flexibility Study.

This module handles all data validation and filtering operations,
separating validation logic from fetching to improve modularity.

Includes:
- Schema validation (required columns, types)
- Data filtering (age, MMSE, nulls)
- Exclusion logging
- Cleaning pipeline
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
import numpy as np

# Import shared exceptions and config
try:
    from config import get_config, get_mmse_threshold, get_env_bool
    from utils import setup_logging, log_info, log_warning, log_error, compute_sha256
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_config, get_mmse_threshold, get_env_bool
    from utils import setup_logging, log_info, log_warning, log_error, compute_sha256

# Re-define exceptions if not imported (should be in ingestion.py or fetcher.py)
class DataFetchError(Exception):
    pass
class DataGapError(Exception):
    pass

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['age', 'stimulus_type', 'perseverative_errors', 'categories_completed']
OPTIONAL_COLUMNS = ['MMSE', 'participant_id']

def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that the DataFrame contains required columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing.append(col)
    
    is_valid = len(missing) == 0
    if not is_valid:
        log_error(logger, f"Schema validation failed. Missing columns: {missing}")
    else:
        log_info(logger, "Schema validation passed.")
    
    return is_valid, missing

def validate_and_filter_dataset(df: pd.DataFrame, metadata: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main validation and filtering pipeline.
    
    Steps:
    1. Validate schema (required columns).
    2. Filter by age >= 65.
    3. Filter by non-null scores.
    4. Filter by MMSE >= 24 (if MMSE column exists).
    5. Generate exclusion log.
    
    Args:
        df: Raw DataFrame.
        metadata: Dataset metadata.
        
    Returns:
        Tuple of (cleaned_df, updated_metadata)
        
    Raises:
        DataFetchError: If schema is invalid.
    """
    log_info(logger, "Starting validation and filtering pipeline.")
    
    # 1. Schema Validation
    is_valid, missing_cols = validate_schema(df)
    if not is_valid:
        raise DataFetchError(f"Invalid schema. Missing columns: {missing_cols}")
    
    # Initialize exclusion counts
    exclusion_counts = {
        "ERR_MISSING_AGE_FIELD": 0,
        "ERR_MISSING_SCORE": 0,
        "ERR_MMSE_IMPAIRED": 0,
        "total_raw": len(df)
    }
    
    # 2. Age Filtering (>= 65)
    initial_count = len(df)
    if 'age' not in df.columns:
        log_error(logger, "ERR_MISSING_AGE_FIELD: 'age' column not found.")
        exclusion_counts["ERR_MISSING_AGE_FIELD"] = initial_count
        df = df.iloc[:0] # Empty dataframe
    else:
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        df_before = df.copy()
        df = df[df['age'] >= 65]
        excluded = len(df_before) - len(df)
        exclusion_counts["ERR_MISSING_AGE_FIELD"] = excluded # Reusing key for age filter as per task T012a
        log_info(logger, f"Age filter: Excluded {excluded} records (age < 65 or null).")
    
    if len(df) == 0:
        log_warning(logger, "No records remaining after age filtering.")
        # Still proceed to generate exclusion log
    
    # 3. Score Filtering (non-null)
    score_cols = ['perseverative_errors', 'categories_completed']
    df_before = df.copy()
    # Check for nulls in score columns
    mask = df[score_cols].notna().all(axis=1)
    df = df[mask]
    excluded = len(df_before) - len(df)
    exclusion_counts["ERR_MISSING_SCORE"] = excluded
    log_info(logger, f"Score filter: Excluded {excluded} records with null scores.")
    
    if len(df) == 0:
        log_warning(logger, "No records remaining after score filtering.")
    
    # 4. MMSE Filtering (if column exists)
    mmse_threshold = get_mmse_threshold()
    if 'MMSE' in df.columns:
        df['MMSE'] = pd.to_numeric(df['MMSE'], errors='coerce')
        df_before = df.copy()
        df = df[df['MMSE'] >= mmse_threshold]
        excluded = len(df_before) - len(df)
        exclusion_counts["ERR_MMSE_IMPAIRED"] = excluded
        log_info(logger, f"MMSE filter (threshold={mmse_threshold}): Excluded {excluded} records.")
    else:
        log_warning(logger, "MMSE column not found. Skipping MMSE filter.")
        # T013b logic: Set flag in metadata
        metadata['has_mmse'] = False
    metadata['has_mmse'] = 'MMSE' in df.columns if 'has_mmse' not in metadata else metadata['has_mmse']
    
    # 5. Update Metadata
    metadata['valid_records'] = len(df)
    metadata['exclusion_counts'] = exclusion_counts
    
    # 6. Generate Exclusion Log
    save_exclusion_log(exclusion_counts)
    
    log_info(logger, f"Validation complete. {len(df)} records remaining.")
    return df, metadata

def save_exclusion_log(counts: Dict[str, Any]) -> None:
    """
    Save exclusion counts to data/processed/exclusion_log.json.
    
    Args:
        counts: Dictionary of exclusion counts.
    """
    output_path = Path("data/processed/exclusion_log.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(counts, f, indent=2)
    log_info(logger, f"Exclusion log saved to {output_path}")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform final cleaning: ensure types, handle participant_id.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Cleaned DataFrame.
    """
    # Ensure participant_id exists
    if 'participant_id' not in df.columns:
        df['participant_id'] = [f"P{i:04d}" for i in range(len(df))]
    
    # Ensure stimulus_type is string
    if 'stimulus_type' in df.columns:
        df['stimulus_type'] = df['stimulus_type'].astype(str)
    
    # Ensure numeric columns are numeric
    num_cols = ['age', 'perseverative_errors', 'categories_completed', 'MMSE']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_validity_metrics(raw_count: int, valid_count: int) -> Dict[str, Any]:
    """
    Calculate validity metrics.
    
    Args:
        raw_count: Total raw records.
        valid_count: Total valid records.
        
    Returns:
        Dictionary of metrics.
    """
    percentage = (valid_count / raw_count * 100) if raw_count > 0 else 0.0
    metrics = {
        "total_raw": raw_count,
        "total_valid": valid_count,
        "validity_percentage": round(percentage, 2),
        "target_met": percentage >= 90.0 # SC-001
    }
    return metrics

def save_validity_metrics(metrics: Dict[str, Any]) -> None:
    """
    Save validity metrics to data/processed/validity_metrics.json.
    """
    output_path = Path("data/processed/validity_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info(logger, f"Validity metrics saved to {output_path}")
