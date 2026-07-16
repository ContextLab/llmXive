import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import numpy as np

from .config import _PROJECT_ROOT, get_min_sample_size
from .logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_csv_file(file_path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path)

def load_otu_table(file_path: Path) -> pd.DataFrame:
    """Load an OTU table CSV."""
    return load_csv_file(file_path)

def filter_complete_records(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter out rows with missing values in required columns or any column if not specified.
    """
    if required_columns:
        # Drop rows where any of the required columns are NA
        df_filtered = df.dropna(subset=required_columns)
    else:
        # Drop rows with any NA
        df_filtered = df.dropna()
    
    excluded_count = len(df) - len(df_filtered)
    if excluded_count > 0:
        logger.info(f"Filtered out {excluded_count} rows with missing values.")
    return df_filtered

def validate_titer_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate titer columns exist and are numeric.
    Filters out rows where titers are non-numeric or invalid (e.g., < 1:10 if that's a hard rule, 
    though task T013 handles specific LOD logic later, this ensures basic validity).
    """
    # Check for presence of expected titer columns if they exist in the dataset
    titer_cols = [c for c in df.columns if 'titer' in c.lower()]
    
    for col in titer_cols:
        if col not in df.columns:
            continue
        
        # Ensure numeric
        original_len = len(df)
        df[col] = pd.to_numeric(df[col], errors='coerce')
        dropped = original_len - len(df.dropna(subset=[col]))
        
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows due to non-numeric values in {col}")
    
    return df

def ensure_minimum_sample_size(df: pd.DataFrame, min_size: int = 50) -> None:
    """
    Ensure the dataframe has at least min_size rows.
    Raises ValueError if not.
    """
    n = len(df)
    if n < min_size:
        raise ValueError(f"ERR_NO_DATA: Insufficient Sample Size (N={n} < {min_size})")

def load_and_preprocess_data(otu_path: Path, meta_path: Path) -> pd.DataFrame:
    """
    Load OTU and metadata, merge, and perform basic cleaning.
    This is a helper for cases where Strategy A/B logic is abstracted differently,
    but T011a implements specific logic in 01_ingest.py.
    """
    otu_df = load_otu_table(otu_path)
    meta_df = load_csv_file(meta_path)
    
    # Merge logic (simplified)
    common_cols = set(otu_df.columns) & set(meta_df.columns)
    if not common_cols:
        raise ValueError("No common columns to merge OTU and metadata.")
    
    merge_key = list(common_cols)[0]
    merged = pd.merge(otu_df, meta_df, on=merge_key, how='inner')
    return merged
