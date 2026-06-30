"""
Preprocessing module for ILI data.
Handles missing weeks (removal), log-transformation, and standardization.
"""
import os
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional

from main import load_config
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

def load_ili_data(filepath: str) -> pd.DataFrame:
    """
    Load the raw ILI CSV data.
    Expects columns: 'week', 'ili' (or similar numeric column for ILI rate).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    # Attempt to read; assume standard CDC FluView format or similar
    # The specific column names might vary, so we look for 'ili' or 'num_ili'
    df = pd.read_csv(filepath)
    
    # Normalize column names to lowercase for consistency
    df.columns = df.columns.str.lower().str.strip()
    
    # Identify the ILI column
    ili_col = None
    for col in ['ili', 'num_ili', 'ili_percent', 'percent_ili']:
        if col in df.columns:
            ili_col = col
            break
    
    if ili_col is None:
        raise ValueError(f"Could not identify ILI column in {filepath}. Available columns: {list(df.columns)}")
    
    # Identify week column
    week_col = None
    for col in ['week', 'epi_week', 'date', 'start_date']:
        if col in df.columns:
            week_col = col
            break
    
    if week_col is None:
        raise ValueError(f"Could not identify week column in {filepath}. Available columns: {list(df.columns)}")
    
    return df, week_col, ili_col

def remove_missing_weeks(df: pd.DataFrame, week_col: str, ili_col: str) -> pd.DataFrame:
    """
    Remove rows where ILI data is missing (NaN).
    Logs the number of rows removed.
    """
    initial_count = len(df)
    df_clean = df.dropna(subset=[ili_col])
    removed_count = initial_count - len(df_clean)
    
    if removed_count > 0:
        logger.warning(f"Removed {removed_count} rows with missing ILI data.")
    else:
        logger.info("No missing ILI data found.")
    
    return df_clean

def log_transform(df: pd.DataFrame, ili_col: str) -> pd.DataFrame:
    """
    Apply log-transform to the ILI column.
    Handles zeros by adding a small epsilon if necessary, though ILI rates are usually > 0.
    """
    df = df.copy()
    
    # Check for non-positive values which cause log errors
    if (df[ili_col] <= 0).any():
        logger.warning("Found non-positive ILI values. Adding small epsilon for log transformation.")
        df[ili_col] = df[ili_col].clip(lower=1e-6)
    
    df[ili_col] = np.log(df[ili_col])
    logger.info("Applied log transformation to ILI data.")
    return df

def standardize(df: pd.DataFrame, ili_col: str) -> Tuple[pd.DataFrame, float, float]:
    """
    Standardize the ILI column (Z-score normalization).
    Returns the standardized DataFrame and the mean/std used.
    """
    df = df.copy()
    mean_val = df[ili_col].mean()
    std_val = df[ili_col].std()
    
    if std_val == 0:
        logger.warning("Standard deviation is zero. Cannot standardize. Returning raw log-transformed data.")
        return df, mean_val, std_val
    
    df[ili_col] = (df[ili_col] - mean_val) / std_val
    logger.info(f"Standardized ILI data (mean={mean_val:.4f}, std={std_val:.4f}).")
    return df, mean_val, std_val

def save_processed_data(df: pd.DataFrame, output_path: str, week_col: str, ili_col: str):
    """
    Save the processed DataFrame to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

def preprocess_pipeline(input_path: str, output_path: str, config_path: Optional[str] = None):
    """
    Run the full preprocessing pipeline:
    1. Load data
    2. Remove missing weeks
    3. Log-transform
    4. Standardize
    5. Save results
    """
    # Load config if provided (though this task is mostly data processing)
    config = load_config(config_path) if config_path else {}
    
    logger.info(f"Starting preprocessing pipeline for {input_path}")
    
    # 1. Load
    df, week_col, ili_col = load_ili_data(input_path)
    logger.info(f"Loaded {len(df)} rows. Week col: {week_col}, ILI col: {ili_col}")
    
    # 2. Remove missing
    df = remove_missing_weeks(df, week_col, ili_col)
    
    # 3. Log transform
    df = log_transform(df, ili_col)
    
    # 4. Standardize
    df, mean_val, std_val = standardize(df, ili_col)
    
    # 5. Save
    save_processed_data(df, output_path, week_col, ili_col)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return df

def main():
    """
    Entry point for running the preprocessing script.
    Expects input from data/raw/fluview_ili.csv and outputs to data/processed/ili_processed.csv
    """
    setup_logging()
    config = load_config()
    
    input_path = "data/raw/fluview_ili.csv"
    output_path = "data/processed/ili_processed.csv"
    
    # Check if input exists (T009 validation should have caught this, but double check)
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Ensure T012a has run.")
        return
    
    try:
        preprocess_pipeline(input_path, output_path)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()