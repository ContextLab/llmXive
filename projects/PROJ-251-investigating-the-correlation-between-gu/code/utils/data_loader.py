import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd
import numpy as np

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_csv_file(filepath: Path) -> pd.DataFrame:
    """Loads a CSV file into a DataFrame."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return pd.read_csv(filepath)

def load_otu_table(filepath: Path) -> pd.DataFrame:
    """Loads an OTU table CSV."""
    df = load_csv_file(filepath)
    # Ensure subject_id is string
    df["subject_id"] = df["subject_id"].astype(str)
    return df

def filter_complete_records(df: pd.DataFrame, required_cols: List[str]) -> pd.DataFrame:
    """Filters out rows with missing values in required columns."""
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    final_count = len(df)
    if initial_count != final_count:
        logger.info(f"Dropped {initial_count - final_count} records due to missing values in {required_cols}")
    return df

def validate_titer_values(df: pd.DataFrame) -> bool:
    """Validates that titer columns are numeric and non-negative."""
    titer_cols = ["titer_baseline", "titer_post"]
    for col in titer_cols:
        if col not in df.columns:
            return False
        if not pd.api.types.is_numeric_dtype(df[col]):
            return False
        if (df[col] < 0).any():
            return False
    return True

def ensure_minimum_sample_size(df: pd.DataFrame, min_size: int = 50) -> bool:
    """Checks if the DataFrame meets the minimum sample size."""
    return len(df) >= min_size

def load_and_preprocess_data(otu_path: Path, serology_path: Path, min_size: int = 50) -> Tuple[pd.DataFrame, bool]:
    """
    Loads and merges OTU and serology data, filters for complete records.
    Returns (merged_df, success).
    """
    try:
        otu_df = load_otu_table(otu_path)
        sero_df = load_csv_file(serology_path)
        
        # Merge
        merged = pd.merge(otu_df, sero_df, on="subject_id", how="inner")
        
        # Filter
        required = ["subject_id", "titer_baseline", "titer_post"]
        merged = filter_complete_records(merged, required)
        
        # Validate
        if not validate_titer_values(merged):
            logger.error("Invalid titer values found")
            return merged, False
        
        # Check size
        if not ensure_minimum_sample_size(merged, min_size):
            logger.warning(f"Sample size {len(merged)} is below minimum {min_size}")
            return merged, False
        
        return merged, True
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return pd.DataFrame(), False
