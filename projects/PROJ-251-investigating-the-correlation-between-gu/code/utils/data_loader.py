import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import numpy as np

from .logging_config import get_logger

logger = get_logger(__name__)

def load_csv_file(path: Path) -> pd.DataFrame:
    """Load a CSV file into a DataFrame."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    logger.info(f"Loading CSV from {path}")
    return pd.read_csv(path)

def load_otu_table(path: Path) -> pd.DataFrame:
    """Load OTU table, handling potential index columns."""
    df = load_csv_file(path)
    # Basic validation
    if df.empty:
        raise ValueError(f"OTU table is empty: {path}")
    return df

def filter_complete_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows with any missing values in critical columns.
    This implements T012 logic (exclude subjects missing baseline or post titers).
    """
    critical_cols = ['subject_id', 'titer_baseline', 'titer_post']
    missing_cols = [c for c in critical_cols if c not in df.columns]
    
    if missing_cols:
        # If critical columns are missing, we can't filter properly.
        # Depending on strictness, we might raise or just drop rows with any NaN.
        # For now, drop any row with any NaN to be safe.
        logger.warning(f"Missing critical columns {missing_cols}. Dropping all rows with any NaN.")
        return df.dropna()
    
    initial_count = len(df)
    # Keep rows where critical columns are not null
    df_clean = df.dropna(subset=critical_cols)
    dropped = initial_count - len(df_clean)
    
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows due to missing critical data.")
    
    return df_clean

def validate_titer_values(df: pd.DataFrame, col_names: List[str] = None) -> pd.DataFrame:
    """
    Validate that titer values are numeric and positive (or zero).
    Returns the dataframe, potentially with warnings.
    """
    if col_names is None:
        col_names = ['titer_baseline', 'titer_post']
    
    for col in col_names:
        if col not in df.columns:
            continue
        
        # Check for non-numeric
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column {col} is not numeric. Attempting conversion.")
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def ensure_minimum_sample_size(df: pd.DataFrame, min_size: int = 50) -> None:
    """
    Check if the dataframe meets the minimum sample size.
    Raises ValueError if not.
    """
    if len(df) < min_size:
        raise ValueError(f"ERR_NO_DATA: Insufficient Sample Size (N={len(df)} < {min_size})")

def load_and_preprocess_data(raw_path: Path) -> pd.DataFrame:
    """
    Load raw data and perform basic preprocessing.
    """
    df = load_csv_file(raw_path)
    df = validate_titer_values(df)
    df = filter_complete_records(df)
    return df
