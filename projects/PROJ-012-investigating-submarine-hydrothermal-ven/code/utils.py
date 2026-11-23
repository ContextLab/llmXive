"""
Utility functions for the Submarine Hydrothermal Vent Microbial Communities project.

Provides:
- Logging infrastructure configuration
- pH outlier detection (FR-006)
- pH heterogeneity calculation (FR-001.1)
"""
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Union, Dict, Any
import pandas as pd
import numpy as np


# --- Logging Infrastructure ---

_logger_registry: Dict[str, logging.Logger] = {}
_log_handlers_set: bool = False

def _ensure_log_handlers() -> None:
    """Initialize root logger handlers if not already set."""
    global _log_handlers_set
    if _log_handlers_set:
        return
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    _log_handlers_set = True

def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configure the root logger and return a named logger.
    
    Args:
        log_file: Optional path to a log file. If provided, a file handler is added.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    
    Returns:
        A configured logger instance.
    """
    _ensure_log_handlers()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Avoid adding duplicate file handlers if called multiple times
        file_handler_exists = any(
            isinstance(h, logging.FileHandler) for h in root_logger.handlers
        )
        if not file_handler_exists:
            file_handler = logging.FileHandler(str(log_path))
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            root_logger.addHandler(file_handler)
    
    return logging.getLogger('hydrothermal_vent')

def get_logger(name: str = 'hydrothermal_vent') -> logging.Logger:
    """
    Retrieve a logger by name.
    
    Args:
        name: Logger name. Defaults to 'hydrothermal_vent'.
    
    Returns:
        Configured logger instance.
    """
    _ensure_log_handlers()
    return logging.getLogger(name)

def setup_ingestion_logging(
    log_file: Optional[Union[str, Path]] = None
) -> logging.Logger:
    """
    Configure specific logging for ingestion steps.
    
    Args:
        log_file: Optional path to ingestion-specific log file.
    
    Returns:
        Logger configured for ingestion tasks.
    """
    logger = setup_logging(log_file=log_file, level=logging.DEBUG)
    logger.info("Ingestion logging initialized.")
    return logger


# --- Outlier Detection (FR-006) ---

def detect_ph_outliers(
    df: pd.DataFrame,
    ph_col: str = 'pH',
    timestamp_col: str = 'timestamp',
    id_col: str = 'sample_id'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect pH outliers and flag samples for review per FR-006.
    
    Rules:
    - pH < 1.0 or pH > 10.0: Flag as extreme outlier (exclude).
    - pH in [1.0, 2.0] (approx unity to moderate acidic): Flag for review.
    - pH in [8.5, 10.0] (edge alkaline range): Flag for review.
    
    Args:
        df: DataFrame containing pH data.
        ph_col: Name of the pH column.
        timestamp_col: Name of the timestamp column (for context).
        id_col: Name of the sample ID column.
    
    Returns:
        Tuple of (cleaned_df, review_df):
        - cleaned_df: Samples with pH in normal range (1.0 <= pH <= 8.5).
        - review_df: Samples flagged for manual review (edge ranges or extreme outliers).
    """
    if ph_col not in df.columns:
        raise ValueError(f"Column '{ph_col}' not found in DataFrame.")
    
    df = df.copy()
    
    # Define ranges
    extreme_low = df[ph_col] < 1.0
    extreme_high = df[ph_col] > 10.0
    review_acidic = (df[ph_col] >= 1.0) & (df[ph_col] <= 2.0)
    review_alkaline = (df[ph_col] >= 8.5) & (df[ph_col] <= 10.0)
    
    # Flagging logic
    is_extreme = extreme_low | extreme_high
    is_review = review_acidic | review_alkaline
    
    df['is_extreme_outlier'] = is_extreme
    df['needs_review'] = is_review
    
    # Categorize
    df['status'] = 'valid'
    df.loc[is_extreme, 'status'] = 'extreme_outlier'
    df.loc[is_review, 'status'] = 'needs_review'
    
    # Split DataFrames
    cleaned_df = df[df['status'] == 'valid'].drop(columns=['is_extreme_outlier', 'needs_review', 'status'])
    review_df = df[df['status'] != 'valid'][[id_col, timestamp_col, ph_col, 'status']].copy()
    
    return cleaned_df, review_df


# --- pH Heterogeneity Calculation (FR-001.1) ---

def calculate_ph_heterogeneity(
    df: pd.DataFrame,
    ph_col: str = 'pH',
    timestamp_col: str = 'timestamp',
    id_col: str = 'sample_id',
    window_minutes: int = 15,
    sd_threshold: float = 0.2
) -> pd.DataFrame:
    """
    Calculate pH heterogeneity (SD) within a ±15 minute window per sample.
    
    Per FR-001.1: Flags samples where SD within the window exceeds a threshold.
    
    Args:
        df: DataFrame with pH and timestamp data.
        ph_col: Name of the pH column.
        timestamp_col: Name of the timestamp column.
        id_col: Name of the sample ID column (or group identifier).
        window_minutes: Time window size in minutes (default 15).
        sd_threshold: Standard deviation threshold for flagging heterogeneity.
    
    Returns:
        DataFrame with added 'pH_sd' and 'pH_heterogeneous' columns.
    """
    if ph_col not in df.columns or timestamp_col not in df.columns:
        raise ValueError(f"Required columns '{ph_col}' and '{timestamp_col}' not found.")
    
    df = df.copy()
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        except Exception as e:
            raise ValueError(f"Failed to parse timestamps in column '{timestamp_col}': {e}")
    
    # Sort by timestamp for windowing
    df = df.sort_values(by=timestamp_col)
    
    def calculate_window_sd(group: pd.DataFrame) -> float:
        """Calculate SD of pH values within the group's time window."""
        if len(group) < 2:
            return 0.0
        return group[ph_col].std()
    
    # Group by sample_id (or relevant grouping key)
    # If id_col is unique per row, we need to look at neighbors within the window
    # The task implies "SD within ±15 min window" for a given sample context.
    # We assume rows are measurements. If 'sample_id' represents a deployment event or site,
    # we group by that. If 'sample_id' is a unique measurement, we calculate SD of neighbors.
    # Based on T010/T011 context: "join samples within ±15 minute window".
    # We will group by 'deployment_event' or similar if available, otherwise by proximity.
    # However, the function signature only takes id_col. Let's assume id_col groups the measurements.
    
    if id_col in df.columns:
        grouped = df.groupby(id_col)
        df['pH_sd'] = grouped[ph_col].transform(lambda x: x.rolling(
            window=f'{window_minutes}T', 
            on=timestamp_col, 
            center=True, 
            min_periods=2
        ).std() if len(x) > 1 else 0.0)
    else:
        # Fallback: rolling window on the whole dataset if no group ID
        # This might be less accurate if multiple sites are mixed, but fits the signature.
        df['pH_sd'] = df[ph_col].rolling(
            window=f'{window_minutes}T', 
            on=timestamp_col, 
            center=True, 
            min_periods=2
        ).std()
    
    # Fill NaN with 0 (single points or edges)
    df['pH_sd'] = df['pH_sd'].fillna(0.0)
    
    # Flag heterogeneity
    df['pH_heterogeneous'] = df['pH_sd'] > sd_threshold
    
    return df


def main():
    """
    Main entry point for testing utility functions.
    """
    logger = setup_logging(log_file='state/utils_test.log', level=logging.DEBUG)
    logger.info("Running utils.py self-test...")
    
    # Test Data
    data = {
        'sample_id': [f'S{i}' for i in range(10)],
        'timestamp': pd.date_range(start='2023-01-01 12:00', periods=10, freq='5min'),
        'pH': [7.0, 7.2, 1.5, 0.5, 9.5, 8.8, 7.5, 7.6, 12.0, 8.0]
    }
    df = pd.DataFrame(data)
    
    # Test Outlier Detection
    logger.info("Testing detect_ph_outliers...")
    cleaned, review = detect_ph_outliers(df)
    logger.debug(f"Cleaned samples: {len(cleaned)}, Review samples: {len(review)}")
    assert len(review) > 0, "Should flag edge/extreme values."
    
    # Test Heterogeneity
    logger.info("Testing calculate_ph_heterogeneity...")
    df_het = calculate_ph_heterogeneity(df, window_minutes=15, sd_threshold=0.5)
    logger.debug(f"Heterogeneous samples: {df_het['pH_heterogeneous'].sum()}")
    
    logger.info("Self-test completed successfully.")

if __name__ == '__main__':
    main()