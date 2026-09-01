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

logger = get_logger(__name__)

# Constants
MIN_DATA_LENGTH = 20
GDelt_INPUT_PATH = "data/raw/gdelt_events.csv"
TRENDS_INPUT_PATH = "data/raw/google_trends.csv"
ALIGNED_OUTPUT_PATH = "data/processed/aligned_timeseries.csv"
STATIONARITY_OUTPUT_PATH = "data/processed/stationarity_check.csv"


def load_gdelt_data(path: str = GDelt_INPUT_PATH) -> pd.DataFrame:
    """Load and parse GDELT events data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"GDELT data file not found: {path}")
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def load_google_trends_data(path: str = TRENDS_INPUT_PATH) -> pd.DataFrame:
    """Load and parse Google Trends data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Google Trends data file not found: {path}")
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """Align two time series to their intersection of dates."""
    logger.info("Aligning timestamps to intersection...")
    
    # Ensure date columns are datetime
    gdelt_df = gdelt_df.copy()
    trends_df = trends_df.copy()
    
    # Set date as index for alignment
    gdelt_df = gdelt_df.set_index('date')
    trends_df = trends_df.set_index('date')
    
    # Select relevant columns (assuming 'value' is the column name)
    # Adjust column names based on actual schema if needed
    gdelt_series = gdelt_df['value'].rename('news_volume')
    trends_series = trends_df['value'].rename('anxiety_trend')
    
    # Inner join to get intersection
    aligned = pd.concat([gdelt_series, trends_series], axis=1)
    aligned = aligned.dropna(how='all')
    
    # Interpolate ONLY missing values (NaN), NOT zeros
    # Linear interpolation for NaN
    aligned = aligned.interpolate(method='linear')
    
    # Fill any remaining NaN at edges with nearest valid value (edge handling)
    aligned = aligned.bfill().ffill()
    
    logger.info(f"Aligned data shape: {aligned.shape}")
    return aligned


def test_stationarity(series: pd.Series, name: str = "Series") -> Tuple[float, bool]:
    """Run Augmented Dickey-Fuller test on a series."""
    result = adfuller(series.dropna())
    p_value = result[1]
    is_stationary = p_value < 0.05
    logger.info(f"{name} ADF p-value: {p_value:.4f}, Stationary: {is_stationary}")
    return p_value, is_stationary


def ensure_stationarity(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure series are stationary by differencing if necessary."""
    df = df.copy()
    for col in df.columns:
        p_val, is_stat = test_stationarity(df[col], col)
        if not is_stat:
            logger.info(f"Differencing {col} to achieve stationarity...")
            df[col] = df[col].diff().dropna()
            # Re-test after differencing
            p_val, is_stat = test_stationarity(df[col], f"{col} (diff)")
            if not is_stat:
                logger.warning(f"{col} still non-stationary after differencing. Proceeding anyway.")
    # Drop any NaNs resulting from differencing
    df = df.dropna()
    return df


def normalize_to_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Apply z-score normalization to all columns."""
    df = df.copy()
    for col in df.columns:
        mean = df[col].mean()
        std = df[col].std()
        if std == 0:
            logger.warning(f"Standard deviation is 0 for {col}. Setting z-scores to 0.")
            df[col] = 0.0
        else:
            df[col] = (df[col] - mean) / std
    return df


def validate_data_length(df: pd.DataFrame, min_length: int = MIN_DATA_LENGTH) -> bool:
    """
    Validate that the time series has sufficient length for Granger causality.
    Returns True if length >= min_length, False otherwise.
    """
    length = len(df)
    logger.info(f"Validating data length: {length} rows (min required: {min_length})")
    if length < min_length:
        logger.error(f"Insufficient data for Granger causality: {length} rows < {min_length}")
        return False
    return True


def save_to_csv(df: pd.DataFrame, path: str) -> None:
    """Save DataFrame to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path)
    logger.info(f"Saved data to {path}")


def main():
    """Main preprocessing pipeline."""
    try:
        # Load data
        logger.info("Loading GDELT data...")
        gdelt_df = load_gdelt_data()
        
        logger.info("Loading Google Trends data...")
        trends_df = load_google_trends_data()
        
        # Align timestamps
        aligned_df = align_timestamps(gdelt_df, trends_df)
        
        # Ensure stationarity
        stationary_df = ensure_stationarity(aligned_df)
        
        # Normalize
        normalized_df = normalize_to_zscore(stationary_df)
        
        # Reset index to have 'date' as a column for output
        normalized_df = normalized_df.reset_index()
        
        # **T022: Validate Data Length**
        if not validate_data_length(normalized_df):
            sys.exit(1)
        
        # Save outputs
        save_to_csv(normalized_df, ALIGNED_OUTPUT_PATH)
        
        # Create stationarity check output (just dates and z-scores)
        stationarity_df = normalized_df[['date', 'news_volume', 'anxiety_trend']].copy()
        stationarity_df.columns = ['date', 'news_zscore', 'anxiety_zscore']
        save_to_csv(stationarity_df, STATIONARITY_OUTPUT_PATH)
        
        logger.info("Preprocessing completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()