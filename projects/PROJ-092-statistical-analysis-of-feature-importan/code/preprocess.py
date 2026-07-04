"""
Preprocessing module for feature importance drift analysis.

Handles missing values via median imputation and splits the dataset
into sequential 30-day windows for time-series analysis.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger, get_logger
from utils.config import get_config

# Ensure logger is configured
logger = setup_logger(__name__)
config = get_config()


def load_raw_dataset() -> pd.DataFrame:
    """
    Loads the raw Electricity Load Diagrams dataset.
    Expects the file to be present in data/raw/ as per T005/T009.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    
    Raises:
        FileNotFoundError: If the dataset file is not found.
    """
    data_dir = Path(config.get("data.raw_dir", "data/raw"))
    # The dataset name from UCI is typically 'ElectricityLoadDiagrams20112014.csv'
    # We look for the most recent .csv file if exact name varies, or use specific name
    target_file = data_dir / "ElectricityLoadDiagrams20112014.csv"
    
    if not target_file.exists():
        # Fallback: try to find any csv in the directory
        csv_files = list(data_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(
                f"No dataset found in {data_dir}. "
                "Please ensure T009 (download.py) has successfully fetched the data."
            )
        target_file = csv_files[0]
        logger.warning(f"Using fallback dataset: {target_file.name}")

    logger.info(f"Loading dataset from {target_file}")
    df = pd.read_csv(target_file)
    
    # Handle potential column name variations or missing 'M' column
    # UCI dataset usually has 'M' (meter ID) and hourly columns (2011-01-01 00:00:00, etc.)
    # We need to ensure we have a timestamp column and numeric data
    return df


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and prepares the dataframe for time-series analysis.
    
    - Converts index to datetime if necessary.
    - Ensures numeric columns are numeric.
    - Sets 'M' (Meter ID) as a separate column if present, or treats rows as time.
    
    The Electricity Load Diagrams dataset has 370 rows (meters) and 35064 columns (hours).
    We need to transpose it so rows are timestamps and columns are meters (features).
    
    Returns:
        pd.DataFrame: Processed dataframe with DatetimeIndex and numeric columns.
    """
    logger.info("Preparing dataframe structure...")
    
    # The UCI dataset format: First column 'M' (ID), then hourly columns.
    # We need to transpose so time is the index.
    if 'M' in df.columns:
        df = df.set_index('M').T
    else:
        # If 'M' is not present, assume all columns are time series
        df = df.T
        
    # Rename columns to M1, M2... if they aren't already
    df.columns = [f"M{c}" for c in range(len(df.columns))]
    
    # Convert index to datetime
    # The columns in the original file are strings like '2011-01-01 00:00:00'
    # After transpose, these become the index
    try:
        df.index = pd.to_datetime(df.index)
    except Exception as e:
        logger.error(f"Failed to convert index to datetime: {e}")
        raise
    
    # Sort by time
    df = df.sort_index()
    
    # Convert all columns to numeric, coercing errors to NaN
    df = df.apply(pd.to_numeric, errors='coerce')
    
    logger.info(f"Dataframe shape after preparation: {df.shape}")
    return df


def handle_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Handles missing values via median imputation.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        Tuple[pd.DataFrame, int]: Imputed dataframe and count of imputed values.
    """
    logger.info("Handling missing values via median imputation...")
    original_df = df.copy()
    
    # Calculate median for each column
    medians = df.median()
    
    # Impute
    df = df.fillna(medians)
    
    # Count imputed values
    missing_count = original_df.isna().sum().sum()
    
    logger.info(f"Imputed {missing_count} missing values using column medians.")
    return df, int(missing_count)


def check_variance(df: pd.DataFrame, threshold: float = 0.0) -> List[str]:
    """
    Checks for zero-variance features and returns a list of columns to drop.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        threshold (float): Minimum variance threshold.
        
    Returns:
        List[str]: List of column names with variance below threshold.
    """
    logger.info("Checking feature variance...")
    variance = df.var()
    zero_var_cols = variance[variance <= threshold].index.tolist()
    
    if zero_var_cols:
        logger.warning(f"Dropping {len(zero_var_cols)} zero-variance features: {zero_var_cols[:5]}...")
    else:
        logger.info("No zero-variance features found.")
        
    return zero_var_cols


def split_into_windows(df: pd.DataFrame, window_days: int = 30) -> List[Tuple[pd.DataFrame, str]]:
    """
    Splits the dataframe into sequential windows based on days.
    
    Args:
        df (pd.DataFrame): Time-indexed dataframe.
        window_days (int): Number of days per window.
        
    Returns:
        List[Tuple[pd.DataFrame, str]]: List of (window_df, window_name) tuples.
    """
    logger.info(f"Splitting data into {window_days}-day windows...")
    
    windows = []
    start_date = df.index.min()
    end_date = df.index.max()
    
    current_start = start_date
    window_count = 0
    
    while current_start < end_date:
        current_end = current_start + pd.Timedelta(days=window_days)
        
        # Clip end to dataset max
        if current_end > end_date:
            current_end = end_date + pd.Timedelta(seconds=1) # Ensure inclusive
        
        # Slice
        window_df = df.loc[current_start:current_end].copy()
        
        if len(window_df) == 0:
            break
            
        window_name = f"Window_{window_count:03d}_{current_start.strftime('%Y-%m-%d')}_to_{(current_start + pd.Timedelta(days=window_days)-pd.Timedelta(seconds=1)).strftime('%Y-%m-%d')}"
        
        windows.append((window_df, window_name))
        
        current_start = current_end + pd.Timedelta(hours=1) # Next window starts after this one? 
        # Actually, standard sliding or chunking. 
        # The task says "sequential 30-day windows". Usually implies non-overlapping chunks for drift detection over time.
        # Let's do non-overlapping chunks: current_start = current_start + window_days
        current_start = current_start + pd.Timedelta(days=window_days) - pd.Timedelta(hours=1) # Overlap? No, let's stick to strict chunks.
        # Correction: If we want sequential non-overlapping:
        # current_start = current_start + pd.Timedelta(days=window_days)
        # But the loop condition `current_start < end_date` and the slice logic needs to be precise.
        
        # Let's restart the loop logic for clarity:
        # We already did one iteration.
        # Reset for the next iteration logic inside the loop is tricky with the `while` condition.
        # Let's use a for loop over date ranges.
        break # Break to rewrite logic below cleanly
    
    # Rewriting the loop for robustness
    windows = []
    current_start = df.index.min()
    window_idx = 0
    
    while current_start < df.index.max():
        current_end = current_start + pd.Timedelta(days=window_days)
        window_df = df.loc[current_start:current_end].copy()
        
        if len(window_df) < 24: # Less than 1 day of data, skip
            break
        
        window_name = f"Window_{window_idx:03d}_{current_start.strftime('%Y-%m-%d')}"
        windows.append((window_df, window_name))
        
        current_start = current_end # Non-overlapping
        window_idx += 1
        
    logger.info(f"Created {len(windows)} windows.")
    return windows


def process_and_save_windows(output_dir: str = "data/processed") -> Dict[str, str]:
    """
    Main entry point for preprocessing.
    1. Loads raw data.
    2. Prepares dataframe (transposes, datetime index).
    3. Imputes missing values.
    4. Checks variance.
    5. Splits into windows.
    6. Saves each window to CSV.
    
    Returns:
        Dict[str, str]: Mapping of window name to file path.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Load
    raw_df = load_raw_dataset()
    
    # Prepare
    df = prepare_dataframe(raw_df)
    
    # Impute
    df, imputed_count = handle_missing_values(df)
    
    # Variance Check (Global first, then per window later in training loop if needed)
    # The task T010 asks to implement variance_check logic. 
    # We can do a global check here or per-window. 
    # T015 mentions "dropped_features list" per window. 
    # We will store the logic here but apply per-window in the main loop if needed.
    # For T010, we focus on the split and imputation.
    
    # Split
    windows = split_into_windows(df, window_days=30)
    
    # Save
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    saved_files = {}
    
    for window_df, name in windows:
        # Check variance per window as per T015 requirement context
        drop_cols = check_variance(window_df)
        if drop_cols:
            window_df = window_df.drop(columns=drop_cols)
        
        file_path = os.path.join(output_dir, f"{name}.csv")
        window_df.to_csv(file_path)
        saved_files[name] = file_path
        logger.info(f"Saved {name} to {file_path} (Shape: {window_df.shape})")
    
    logger.info(f"Preprocessing complete. {len(saved_files)} windows saved.")
    return saved_files


def main():
    """Main entry point for the script."""
    try:
        results = process_and_save_windows()
        print(f"Successfully processed {len(results)} windows.")
        for name, path in results.items():
            print(f"  - {name}: {path}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()