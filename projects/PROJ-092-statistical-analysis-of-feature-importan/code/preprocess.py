import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Generator

from utils.config import get_config
from utils.logger import get_logger

def load_raw_dataset(data_path: Path) -> pd.DataFrame:
    """
    Load the raw dataset from a CSV file.
    
    Args:
        data_path: Path to the CSV file.
        
    Returns:
        DataFrame containing the raw data.
    """
    logger = get_logger("preprocess")
    logger.info(f"Loading raw data from {data_path}...")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns.")
    
    return df

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the DataFrame: ensure correct types, sort by time if applicable.
    
    Args:
        df: Raw DataFrame.
        
    Returns:
        Prepared DataFrame.
    """
    logger = get_logger("preprocess")
    
    # Sort by index if it represents time (assuming numeric or datetime index)
    if df.index.dtype == 'object' or pd.api.types.is_datetime64_any_dtype(df.index):
        df = df.sort_index()
        logger.info("Sorted DataFrame by index.")
    
    return df.reset_index(drop=True)

def handle_missing_values(df: pd.DataFrame, strategy: str = "median") -> pd.DataFrame:
    """
    Handle missing values using the specified strategy.
    
    Args:
        df: DataFrame with missing values.
        strategy: Imputation strategy ('median', 'mean', 'drop').
        
    Returns:
        DataFrame with missing values handled.
    """
    logger = get_logger("preprocess")
    missing_count = df.isnull().sum().sum()
    
    if missing_count == 0:
        logger.info("No missing values found.")
        return df
    
    logger.info(f"Found {missing_count} missing values. Using {strategy} imputation.")
    
    if strategy == "drop":
        df = df.dropna()
    elif strategy == "mean":
        df = df.fillna(df.mean())
    elif strategy == "median":
        df = df.fillna(df.median())
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    logger.info(f"Missing values handled. Remaining rows: {len(df)}.")
    return df

def check_variance(
    df: pd.DataFrame,
    feature_cols: List[str],
    threshold: float = 1e-7
) -> Tuple[List[str], List[str]]:
    """
    Check for zero-variance features and drop them.
    
    Args:
        df: DataFrame.
        feature_cols: List of feature column names.
        threshold: Variance threshold below which features are considered zero-variance.
        
    Returns:
        Tuple of (dropped_features, valid_features).
    """
    logger = get_logger("preprocess")
    dropped = []
    valid = []
    
    for col in feature_cols:
        var = df[col].var()
        if var < threshold:
            dropped.append(col)
        else:
            valid.append(col)
    
    if dropped:
        logger.warning(f"Dropped {len(dropped)} zero-variance features: {dropped}")
    
    return dropped, valid

def split_into_windows(
    df: pd.DataFrame,
    window_size_days: int = 30,
    target_col: Optional[str] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Split the DataFrame into sequential time windows.
    
    Args:
        df: DataFrame with time-indexed or sequential data.
        window_size_days: Size of each window in rows (assuming daily data).
        target_col: Optional target column to exclude from features.
        
    Yields:
        DataFrames for each window.
    """
    logger = get_logger("preprocess")
    total_rows = len(df)
    
    if target_col and target_col in df.columns:
        # Ensure target is at the end for processing
        cols = [c for c in df.columns if c != target_col] + [target_col]
        df = df[cols]
    
    num_windows = total_rows // window_size_days
    
    logger.info(f"Splitting {total_rows} rows into {num_windows} windows of {window_size_days} rows.")
    
    for i in range(num_windows):
        start_idx = i * window_size_days
        end_idx = start_idx + window_size_days
        window_df = df.iloc[start_idx:end_idx].copy()
        yield window_df

def process_and_save_windows(
    df: pd.DataFrame,
    output_dir: Path,
    window_size_days: int = 30,
    target_col: Optional[str] = None
) -> List[Path]:
    """
    Process the DataFrame, split into windows, and save each window to CSV.
    
    Args:
        df: DataFrame to process.
        output_dir: Directory to save window files.
        window_size_days: Size of each window.
        target_col: Optional target column.
        
    Returns:
        List of paths to saved window files.
    """
    logger = get_logger("preprocess")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    window_paths = []
    
    for idx, window_df in enumerate(split_into_windows(df, window_size_days, target_col)):
        window_id = f"window_{idx:03d}"
        window_path = output_dir / f"{window_id}.csv"
        window_df.to_csv(window_path, index=False)
        window_paths.append(window_path)
        logger.info(f"Saved {window_id} to {window_path}")
    
    return window_paths

def main():
    """CLI entry point for preprocessing."""
    try:
        config = get_config()
        base_path = Path(config.get("base_path", "."))
        
        raw_data_path = base_path / config.get("raw_data_file", "data/raw/electricity_load.csv")
        processed_dir = base_path / "data" / "processed"
        
        if not raw_data_path.exists():
            print(f"Raw data file not found: {raw_data_path}")
            sys.exit(1)
        
        logger = get_logger("preprocess")
        
        # Load and process
        df = load_raw_dataset(raw_data_path)
        df = prepare_dataframe(df)
        df = handle_missing_values(df)
        
        # Check variance
        feature_cols = [c for c in df.columns if c != config.get("target_col", "load")]
        dropped, valid = check_variance(df, feature_cols)
        df = df[valid + [config.get("target_col", "load")]]
        
        # Split and save
        window_paths = process_and_save_windows(
            df,
            processed_dir,
            window_size_days=30,
            target_col=config.get("target_col", "load")
        )
        
        print(f"Preprocessing complete. Saved {len(window_paths)} windows.")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()