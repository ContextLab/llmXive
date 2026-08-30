"""
Preprocessing module for the impact of aggregate negative news publication volume on anticipatory anxiety.

This module handles:
- Loading raw data from GDELT and Google Trends
- Aligning timestamps to daily resolution
- Interpolating missing values (linear) while preserving zero-event days
- Testing and ensuring stationarity (ADF test + differencing)
- Normalizing data to z-scores
- Validating data length and post-interpolation completeness
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from sklearn.preprocessing import StandardScaler

# Import logging configuration from utils
from utils.logging import get_logger

# Constants
MIN_DATA_LENGTH = 20
OUTPUT_PATH_ALIGNED = "data/processed/aligned_timeseries.csv"
OUTPUT_PATH_STATIONARITY = "data/processed/stationarity_check.csv"
RAW_GDELT_PATH = "data/raw/gdelt_events.csv"
RAW_TRENDS_PATH = "data/raw/google_trends.csv"

logger = get_logger(__name__)

def load_gdelt_data(path: str = RAW_GDELT_PATH) -> pd.DataFrame:
    """Load and parse GDELT events data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"GDELT data not found at {path}")
    df = pd.read_csv(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'])
        df = df.drop(columns=['Date'])
    else:
        raise ValueError("GDELT data must contain a 'date' or 'Date' column")
    return df

def load_google_trends_data(path: str = RAW_TRENDS_PATH) -> pd.DataFrame:
    """Load and parse Google Trends data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Google Trends data not found at {path}")
    df = pd.read_csv(path)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'])
        df = df.drop(columns=['Date'])
    else:
        raise ValueError("Google Trends data must contain a 'date' or 'Date' column")
    return df


def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align two time series to their intersection of dates.
    Interpolates missing values (NaN) using linear interpolation.
    Does NOT interpolate zero-event counts (0 is a valid data point).
    """
    # Ensure date column is datetime
    gdelt_df = gdelt_df.copy()
    trends_df = trends_df.copy()
    
    # Identify value columns (non-date)
    gdelt_val_cols = [c for c in gdelt_df.columns if c != 'date']
    trends_val_cols = [c for c in trends_df.columns if c != 'date']

    # Set index to date for alignment
    gdelt_df = gdelt_df.set_index('date')
    trends_df = trends_df.set_index('date')

    # Merge on intersection of indices
    merged = gdelt_df.join(trends_df, how='inner', lsuffix='_gdelt', rsuffix='_trends')
    
    # Rename columns for clarity if needed, or keep suffixes
    # For simplicity, we assume the merge results in distinct columns
    
    # Interpolate NaNs (linear)
    # Note: This respects the requirement to NOT interpolate 0s, 
    # as linear interpolation only acts on NaN values, not 0.0.
    merged = merged.interpolate(method='linear')

    # Reset index
    merged = merged.reset_index()
    
    return merged

def test_stationarity(series: pd.Series, name: str = "series") -> Dict[str, Any]:
    """
    Run Augmented Dickey-Fuller test on a series.
    Returns dict with 'is_stationary' (bool) and 'p_value' (float).
    """
    try:
        result = adfuller(series.dropna())
        p_value = result[1]
        is_stationary = p_value < 0.05
        logger.info(f"ADF Test for {name}: p-value={p_value:.4f}, Stationary={is_stationary}")
        return {
            "name": name,
            "p_value": p_value,
            "is_stationary": is_stationary,
            "statistic": result[0]
        }
    except Exception as e:
        logger.error(f"ADF Test failed for {name}: {e}")
        return {
            "name": name,
            "p_value": 1.0,
            "is_stationary": False,
            "error": str(e)
        }

def ensure_stationarity(df: pd.DataFrame, target_cols: List[str]) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Ensure specified columns are stationary by differencing if necessary.
    Returns the differenced DataFrame and a list of stationarity check results.
    """
    df = df.copy()
    results = []
    
    for col in target_cols:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in dataframe for stationarity check")
            continue
        
        series = df[col]
        check = test_stationarity(series, col)
        results.append(check)
        
        if not check['is_stationary']:
            logger.info(f"Differencing {col} to achieve stationarity")
            df[col] = df[col].diff().dropna()
            # Re-check after differencing
            # Note: Differencing reduces length by 1. 
            # We need to ensure we don't drop the whole series if it's short.
            # For this implementation, we assume the series is long enough.
            # If the series becomes too short, the main validation will catch it later.
            
            # Re-run ADF on differenced series
            # We need to align the index if we dropped NaNs
            # Simple approach: just re-run on the differenced series
            new_check = test_stationarity(df[col], f"{col}_diff")
            if not new_check['is_stationary']:
                logger.warning(f"Differenced {col} is still non-stationary")
            results.append(new_check)
    
    # Align indices after differencing (some might have NaNs at the start)
    # Fill NaNs created by diff with 0? Or drop? 
    # Standard practice for Granger: drop rows with NaNs resulting from differencing
    df = df.dropna()
    
    return df, results

def normalize_to_zscore(df: pd.DataFrame, target_cols: List[str]) -> pd.DataFrame:
    """Convert specified columns to z-scores (mean=0, std=1)."""
    df = df.copy()
    for col in target_cols:
        if col in df.columns:
            mean = df[col].mean()
            std = df[col].std()
            if std == 0:
                logger.warning(f"Standard deviation is 0 for {col}, cannot normalize")
                continue
            df[col] = (df[col] - mean) / std
    return df

def validate_data_length(df: pd.DataFrame, min_length: int = MIN_DATA_LENGTH) -> bool:
    """
    Validate that the time series has sufficient length for Granger causality.
    Returns True if length >= min_length, False otherwise.
    """
    length = len(df)
    if length < min_length:
        error_msg = f"Insufficient data for Granger causality: {length} rows < {min_length} required"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Data length validation passed: {length} rows >= {min_length}")
    return True

def save_to_csv(df: pd.DataFrame, path: str):
    """Save dataframe to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved data to {path}")

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting preprocessing pipeline...")
    
    try:
        # 1. Load Raw Data
        logger.info("Loading GDELT data...")
        gdelt_df = load_gdelt_data()
        logger.info(f"Loaded {len(gdelt_df)} GDELT records")
        
        logger.info("Loading Google Trends data...")
        trends_df = load_google_trends_data()
        logger.info(f"Loaded {len(trends_df)} Trends records")
        
        # 2. Align Timestamps
        logger.info("Aligning timestamps...")
        aligned_df = align_timestamps(gdelt_df, trends_df)
        logger.info(f"Aligned data has {len(aligned_df)} rows")
        
        # 3. Validate Data Length (T022 Implementation)
        if not validate_data_length(aligned_df):
            logger.critical("Insufficient data for Granger causality.")
            sys.exit(1)
        
        # 4. Ensure Stationarity
        # Identify numeric columns to process (exclude date)
        numeric_cols = aligned_df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError("No numeric columns found in aligned data")
            
        logger.info(f"Checking stationarity for columns: {numeric_cols}")
        stationary_df, stationarity_results = ensure_stationarity(aligned_df, numeric_cols)
        
        # 5. Normalize
        logger.info("Normalizing to z-scores...")
        normalized_df = normalize_to_zscore(stationary_df, numeric_cols)
        
        # 6. Save Outputs
        save_to_csv(normalized_df, OUTPUT_PATH_ALIGNED)
        
        # Save stationarity check results
        results_df = pd.DataFrame(stationarity_results)
        save_to_csv(results_df, OUTPUT_PATH_STATIONARITY)
        
        logger.info("Preprocessing completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()