import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# Import from sibling modules as per API surface
from download import verify_dataset, download_file
from utils.logger import get_logger
from utils.config import get_config

# Ensure the logger is configured
logger = get_logger(__name__)

def load_raw_dataset(data_dir: Path) -> pd.DataFrame:
    """
    Load the raw dataset from the data directory.
    Expects the file to be present after T009 download.
    """
    config = get_config()
    # The download task (T009) should have placed the file here
    # Based on UCI Electricity Load Diagrams, usually named 'ElectricityLoadDiagrams20112014.txt'
    # or similar. We will look for the first .txt or .csv in the raw dir.
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    files = list(raw_dir.glob("*"))
    if not files:
        raise FileNotFoundError(f"No data files found in {raw_dir}")
    
    # Assume the first file is the dataset (or specifically the one T009 downloaded)
    dataset_path = files[0]
    logger.info(f"Loading dataset from {dataset_path}")
    
    # UCI Electricity Load usually is tab-separated or comma-separated
    # Try to infer or use common delimiters
    try:
        df = pd.read_csv(dataset_path, sep='\t', parse_dates=True, index_col=0)
    except Exception:
        try:
            df = pd.read_csv(dataset_path, sep=',', parse_dates=True, index_col=0)
        except Exception:
            raise ValueError(f"Could not parse dataset at {dataset_path} as CSV/TSV")
    
    return df

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare the dataframe:
    - Ensure index is datetime
    - Handle non-numeric columns if any
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        # Try to convert index if it's not already
        df.index = pd.to_datetime(df.index)
    
    # Select only numeric columns for analysis
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        raise ValueError("No numeric columns found in dataset after cleaning.")
    
    return numeric_df

def handle_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Handle missing values via median imputation.
    Returns the imputed dataframe and a dict of columns with counts of missing values.
    """
    missing_counts = df.isnull().sum().to_dict()
    cols_with_missing = {k: v for k, v in missing_counts.items() if v > 0}
    
    if not cols_with_missing:
        logger.info("No missing values found.")
        return df, cols_with_missing
    
    logger.info(f"Imputing missing values in {len(cols_with_missing)} columns using median.")
    # Median imputation
    df_imputed = df.copy()
    for col, count in cols_with_missing.items():
        median_val = df[col].median()
        if np.isnan(median_val):
            # If median is NaN (e.g., all values are NaN), drop column
            logger.warning(f"Column {col} has all NaN values. Dropping column.")
            df_imputed = df_imputed.drop(columns=[col])
        else:
            df_imputed[col].fillna(median_val, inplace=True)
    
    return df_imputed, cols_with_missing

def check_variance(df: pd.DataFrame, threshold: float = 0.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Check for zero-variance features and drop them.
    Returns the dataframe with zero-variance columns dropped and the list of dropped columns.
    """
    dropped_features = []
    # Calculate variance
    variance = df.var()
    zero_var_cols = variance[variance <= threshold].index.tolist()
    
    if zero_var_cols:
        logger.warning(f"Dropping {len(zero_var_cols)} features with zero or near-zero variance: {zero_var_cols}")
        df = df.drop(columns=zero_var_cols)
        dropped_features = zero_var_cols
    
    return df, dropped_features

def split_into_windows(df: pd.DataFrame, window_size_days: int = 30) -> List[Tuple[str, pd.DataFrame]]:
    """
    Split the dataframe into sequential 30-day windows.
    Returns a list of tuples: (window_id, window_dataframe).
    """
    if df.empty:
        raise ValueError("Cannot split empty dataframe.")
    
    # Ensure index is datetime and sorted
    df = df.sort_index()
    
    windows = []
    start_date = df.index[0]
    end_date = df.index[-1]
    
    current_start = start_date
    window_idx = 1
    
    while current_start < end_date:
        current_end = current_start + pd.Timedelta(days=window_size_days)
        
        # Slice the dataframe
        window_df = df.loc[current_start:current_end]
        
        if window_df.empty:
            break
        
        window_id = f"W{window_idx:03d}"
        windows.append((window_id, window_df))
        
        # Move to next window (non-overlapping sequential)
        current_start = current_end
        window_idx += 1
    
    logger.info(f"Split data into {len(windows)} windows of {window_size_days} days.")
    return windows

def process_and_save_windows(data_dir: Path, output_dir: Path):
    """
    Main orchestration function for preprocessing:
    1. Load raw data
    2. Prepare dataframe
    3. Handle missing values (median imputation)
    4. Check and drop zero-variance features
    5. Split into 30-day windows
    6. Save each window as a CSV in data/processed/
    """
    logger.info("Starting preprocessing pipeline.")
    
    # Load
    raw_df = load_raw_dataset(data_dir)
    
    # Prepare
    clean_df = prepare_dataframe(raw_df)
    
    # Impute
    imputed_df, missing_info = handle_missing_values(clean_df)
    logger.info(f"Missing values handled. Imputed columns: {list(missing_info.keys())}")
    
    # Variance check
    final_df, dropped_features = check_variance(imputed_df)
    if dropped_features:
        logger.info(f"Dropped features: {dropped_features}")
    
    # Split
    windows = split_into_windows(final_df, window_size_days=30)
    
    if not windows:
        raise ValueError("No windows generated from data.")
    
    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    for window_id, window_df in windows:
        output_path = output_dir / f"{window_id}.csv"
        window_df.to_csv(output_path)
        logger.info(f"Saved window {window_id} to {output_path}")
    
    # Save metadata about the preprocessing steps
    metadata = {
        "total_windows": len(windows),
        "window_size_days": 30,
        "imputed_columns": list(missing_info.keys()),
        "dropped_features": dropped_features,
        "original_shape": list(raw_df.shape),
        "final_shape": list(final_df.shape)
    }
    
    metadata_path = output_dir / "preprocessing_metadata.json"
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Preprocessing complete. Metadata saved to {metadata_path}")

def main():
    """Entry point for the preprocessing script."""
    # Setup paths
    config = get_config()
    data_dir = Path(config.data_dir)
    output_dir = Path(config.processed_dir)
    
    try:
        process_and_save_windows(data_dir, output_dir)
        logger.info("Preprocessing finished successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()