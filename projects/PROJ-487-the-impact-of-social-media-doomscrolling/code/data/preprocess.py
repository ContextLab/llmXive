import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller

from utils.logging import get_logger
from utils.validation import validate_against_schema, load_schema

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
SCHEMA_PATH = os.path.join(PROJECT_ROOT, 'specs', '001-news-volume-anxiety', 'contracts', 'dataset.schema.yaml')

# Threshold for minimum data length for Granger causality
MIN_DATA_LENGTH = 20

def load_gdelt_data(file_path: str) -> pd.DataFrame:
    """Load GDELT events data from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"GDELT data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def load_google_trends_data(file_path: str) -> pd.DataFrame:
    """Load Google Trends data from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Google Trends data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """Align timestamps by taking intersection of dates."""
    # Set date as index for alignment
    gdelt_indexed = gdelt_df.set_index('date')
    trends_indexed = trends_df.set_index('date')
    
    # Align to intersection
    aligned = gdelt_indexed.join(trends_indexed, how='inner')
    
    # Reset index to get date back as column
    aligned = aligned.reset_index()
    
    # Interpolate missing values (NaN) using linear interpolation
    # Do NOT interpolate zero-event counts (0 is a valid data point)
    numeric_cols = aligned.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        # Only interpolate NaN values, leave 0s as is
        aligned[col] = aligned[col].interpolate(method='linear', limit_direction='both')
    
    return aligned

def test_stationarity(series: pd.Series) -> Tuple[float, str]:
    """Run Augmented Dickey-Fuller test on a time series."""
    result = adfuller(series.dropna())
    p_value = result[1]
    status = "stationary" if p_value < 0.05 else "non-stationary"
    return p_value, status

def ensure_stationarity(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply differencing until the series is stationary."""
    df = df.copy()
    series = df[column]
    
    p_value, status = test_stationarity(series)
    logger.info(f"Column {column}: p-value={p_value:.4f}, status={status}")
    
    if status == "non-stationary":
        # Apply differencing
        df[column] = df[column].diff()
        # Drop NaN resulting from differencing
        df = df.dropna()
        logger.info(f"Applied differencing to {column}")
        
        # Re-test after differencing
        p_value, status = test_stationarity(df[column])
        logger.info(f"After differencing - Column {column}: p-value={p_value:.4f}, status={status}")
    
    return df

def normalize_to_zscore(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Apply z-score normalization to specified columns."""
    df = df.copy()
    for col in columns:
        mean = df[col].mean()
        std = df[col].std()
        if std == 0:
            logger.warning(f"Standard deviation is 0 for column {col}, skipping normalization")
            continue
        df[col] = (df[col] - mean) / std
    return df

def validate_data_length(df: pd.DataFrame) -> bool:
    """
    Validate that the time-series has sufficient length for Granger causality testing.
    Returns True if length >= MIN_DATA_LENGTH, otherwise exits with code 1.
    """
    length = len(df)
    logger.info(f"Validating data length: {length} rows")
    
    if length < MIN_DATA_LENGTH:
        error_msg = f"Insufficient data for Granger causality"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    logger.info(f"Data length check passed: {length} >= {MIN_DATA_LENGTH}")
    return True

def save_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """Save DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved data to {output_path}")

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting data preprocessing pipeline")
    
    # Define file paths
    gdelt_path = os.path.join(DATA_DIR, 'raw', 'gdelt_events.csv')
    trends_path = os.path.join(DATA_DIR, 'raw', 'google_trends.csv')
    aligned_output = os.path.join(PROCESSED_DIR, 'aligned_timeseries.csv')
    stationarity_output = os.path.join(PROCESSED_DIR, 'stationarity_check.csv')
    
    # Load data
    logger.info("Loading GDELT data")
    gdelt_df = load_gdelt_data(gdelt_path)
    
    logger.info("Loading Google Trends data")
    trends_df = load_google_trends_data(trends_path)
    
    # Align timestamps
    logger.info("Aligning timestamps")
    aligned_df = align_timestamps(gdelt_df, trends_df)
    
    # Validate data length BEFORE proceeding
    logger.info("Validating data length for Granger causality")
    validate_data_length(aligned_df)
    
    # Ensure stationarity for both series
    # Assuming columns are named appropriately after alignment
    # We need to identify the value columns
    value_cols = [col for col in aligned_df.columns if col != 'date' and aligned_df[col].dtype in [np.float64, np.int64]]
    
    if len(value_cols) < 2:
        logger.error("Expected at least two value columns after alignment")
        sys.exit(1)
    
    news_col = value_cols[0]
    anxiety_col = value_cols[1]
    
    logger.info(f"Processing stationarity for {news_col} and {anxiety_col}")
    aligned_df = ensure_stationarity(aligned_df, news_col)
    aligned_df = ensure_stationarity(aligned_df, anxiety_col)
    
    # Normalize to z-score
    logger.info("Normalizing to z-scores")
    aligned_df = normalize_to_zscore(aligned_df, [news_col, anxiety_col])
    
    # Create stationarity check output
    stationarity_df = aligned_df[['date', news_col, anxiety_col]].copy()
    stationarity_df.columns = ['date', 'news_zscore', 'anxiety_zscore']
    
    # Save outputs
    logger.info("Saving aligned timeseries")
    save_to_csv(aligned_df, aligned_output)
    
    logger.info("Saving stationarity check")
    save_to_csv(stationarity_df, stationarity_output)
    
    logger.info("Preprocessing pipeline completed successfully")
    print(f"Aligned data saved to: {aligned_output}")
    print(f"Stationarity check saved to: {stationarity_output}")

if __name__ == "__main__":
    main()