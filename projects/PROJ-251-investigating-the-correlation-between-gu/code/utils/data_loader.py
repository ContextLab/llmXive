import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union
import pandas as pd
import numpy as np

from utils.logging_config import get_logger
from utils.config import get_lod_value, get_impute_lod, get_min_sample_size, get_use_synthetic_data

logger = get_logger(__name__)

class DataUnavailableError(Exception):
    """Raised when real data cannot be fetched or is insufficient."""
    pass

class InsufficientSampleSizeError(Exception):
    """Raised when the dataset size is below the required minimum."""
    pass

def load_csv_file(filepath: Path) -> pd.DataFrame:
    """Loads a CSV file into a DataFrame.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            raise ValueError(f"File {filepath} is empty")
        return df
    except Exception as e:
        raise ValueError(f"Failed to parse CSV {filepath}: {e}") from e

def load_otu_table(filepath: Path) -> pd.DataFrame:
    """Loads an OTU table CSV and standardizes column types.
    
    Args:
        filepath: Path to the OTU table CSV.
        
    Returns:
        pd.DataFrame: The loaded OTU table with 'subject_id' as string.
    """
    df = load_csv_file(filepath)
    # Ensure subject_id is string for consistent merging
    if "subject_id" in df.columns:
        df["subject_id"] = df["subject_id"].astype(str)
    return df

def filter_complete_records(df: pd.DataFrame, required_cols: List[str]) -> pd.DataFrame:
    """Filters out rows with missing values (NaN) in required columns.
    
    Args:
        df: Input DataFrame.
        required_cols: List of column names that must not be null.
        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    initial_count = len(df)
    # dropna handles NaN, NaT, but we specifically want to catch missing values
    df_clean = df.dropna(subset=required_cols)
    final_count = len(df_clean)
    
    dropped = initial_count - final_count
    if dropped > 0:
        logger.info(f"Dropped {dropped} records due to missing values in {required_cols}")
    
    return df_clean

def validate_titer_values(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validates that titer columns are numeric and non-negative.
    
    Args:
        df: DataFrame containing titer columns.
        
    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    titer_cols = ["titer_baseline", "titer_post"]
    errors = []
    
    for col in titer_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
            continue
        
        # Check numeric
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column {col} is not numeric")
            continue
        
        # Check non-negative (allowing 0 for LOD handling)
        if (df[col] < 0).any():
            errors.append(f"Column {col} contains negative values")
    
    return len(errors) == 0, errors

def ensure_minimum_sample_size(df: pd.DataFrame, min_size: Optional[int] = None) -> bool:
    """Checks if the DataFrame meets the minimum sample size.
    
    Args:
        df: Input DataFrame.
        min_size: Minimum required rows. If None, uses config default.
        
    Returns:
        bool: True if size is sufficient.
        
    Raises:
        InsufficientSampleSizeError: If size is insufficient and real data is used.
    """
    if min_size is None:
        min_size = get_min_sample_size()
        
    current_size = len(df)
    if current_size < min_size:
        if not get_use_synthetic_data():
            raise InsufficientSampleSizeError(
                f"Insufficient sample size: {current_size} < {min_size}. "
                "Pipeline halted as per real data requirements."
            )
        else:
            logger.warning(f"Synthetic data mode: Sample size {current_size} is below minimum {min_size}. Continuing.")
            return False
    return True

def load_and_preprocess_data(
    otu_path: Path, 
    serology_path: Path, 
    min_size: Optional[int] = None
) -> Tuple[pd.DataFrame, bool]:
    """
    Loads and merges OTU and serology data, filters for complete records,
    and validates basic constraints.
    
    This function performs:
    1. Load OTU table and Serology metadata.
    2. Inner merge on 'subject_id'.
    3. Filter rows with missing critical values (titer_baseline, titer_post).
    4. Validate titer values are numeric and non-negative.
    5. Check minimum sample size (raising error if real data is insufficient).
    
    Args:
        otu_path: Path to the OTU table CSV.
        serology_path: Path to the serology metadata CSV.
        min_size: Minimum sample size threshold.
        
    Returns:
        Tuple[pd.DataFrame, bool]: (Merged DataFrame, success_flag).
        The success_flag is False if validation fails but the DataFrame is returned.
    """
    try:
        logger.info(f"Loading OTU table from {otu_path}")
        otu_df = load_otu_table(otu_path)
        
        logger.info(f"Loading serology data from {serology_path}")
        sero_df = load_csv_file(serology_path)
        
        # Merge
        logger.info("Merging datasets on 'subject_id'")
        merged = pd.merge(otu_df, sero_df, on="subject_id", how="inner")
        
        if merged.empty:
            logger.error("Merge resulted in an empty dataset. Check subject_id consistency.")
            return merged, False
        
        # Filter
        required = ["subject_id", "titer_baseline", "titer_post"]
        merged = filter_complete_records(merged, required)
        
        if merged.empty:
            logger.error("No records remained after filtering for complete titers.")
            return merged, False
        
        # Validate
        is_valid, errors = validate_titer_values(merged)
        if not is_valid:
            logger.error(f"Validation failed: {errors}")
            return merged, False
        
        # Check size
        ensure_minimum_sample_size(merged, min_size)
        
        logger.info(f"Data loading successful. Final count: {len(merged)}")
        return merged, True
        
    except InsufficientSampleSizeError:
        raise
    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        return pd.DataFrame(), False