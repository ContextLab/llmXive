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
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
STATISTICAL_VALIDITY_THRESHOLD = 0.05

def load_gdelt_data(filepath: str) -> pd.DataFrame:
    """Load GDELT events data from CSV."""
    logger.info(f"Loading GDELT data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GDELT data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    return df

def load_google_trends_data(filepath: str) -> pd.DataFrame:
    """Load Google Trends data from CSV."""
    logger.info(f"Loading Google Trends data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Google Trends data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    return df

def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align timestamps from both datasets to daily intervals.
    Preserves zero-event days as valid zeros.
    Uses linear interpolation ONLY for null/missing values.
    """
    logger.info("Aligning timestamps between datasets")
    
    # Set date as index
    gdelt_df = gdelt_df.set_index('date')
    trends_df = trends_df.set_index('date')
    
    # Create a complete daily date range covering both datasets
    full_date_range = pd.date_range(
        start=min(gdelt_df.index.min(), trends_df.index.min()),
        end=max(gdelt_df.index.max(), trends_df.index.max()),
        freq='D'
    )
    
    # Reindex both datasets to full date range
    gdelt_aligned = gdelt_df.reindex(full_date_range)
    trends_aligned = trends_df.reindex(full_date_range)
    
    # Rename columns to avoid conflicts
    gdelt_aligned = gdelt_aligned.rename(columns={'event_count': 'gdelt_event_count'})
    trends_aligned = trends_aligned.rename(columns={
        'anticipatory_anxiety': 'trends_anticipatory_anxiety',
        'worry_about_future': 'trends_worry_about_future'
    })
    
    # Merge aligned datasets
    merged_df = pd.concat([gdelt_aligned, trends_aligned], axis=1)
    
    # Fill NaN values in GDELT count with 0 (zero-event days are valid)
    if 'gdelt_event_count' in merged_df.columns:
        merged_df['gdelt_event_count'] = merged_df['gdelt_event_count'].fillna(0)
    
    # Linear interpolation for missing values in trends data
    trends_cols = ['trends_anticipatory_anxiety', 'trends_worry_about_future']
    for col in trends_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].interpolate(method='linear')
            # Fill any remaining NaNs at edges with nearest valid value
            merged_df[col] = merged_df[col].bfill().ffill()
    
    # Reset index to make date a column again
    merged_df = merged_df.reset_index()
    merged_df = merged_df.rename(columns={'index': 'date'})
    
    logger.info(f"Aligned data shape: {merged_df.shape}")
    return merged_df

def test_stationarity(series: pd.Series, column_name: str = "unknown") -> Dict[str, Any]:
    """
    Perform Augmented Dickey-Fuller (ADF) test for stationarity.
    
    Returns a dictionary with:
    - 'stationary': bool (True if p-value < 0.05)
    - 'p_value': float
    - 'adf_statistic': float
    - 'critical_values': dict
    """
    logger.info(f"Testing stationarity for column: {column_name}")
    
    if len(series) < 10:
        logger.warning(f"Series for {column_name} too short for ADF test ({len(series)} points)")
        return {
            'stationary': False,
            'p_value': 1.0,
            'adf_statistic': np.nan,
            'critical_values': {},
            'message': 'Series too short'
        }
    
    try:
        result = adfuller(series.dropna())
        adf_statistic = result[0]
        p_value = result[1]
        critical_values = result[4]
        
        is_stationary = p_value < STATISTICAL_VALIDITY_THRESHOLD
        
        logger.info(f"ADF Test for {column_name}: p-value={p_value:.4f}, "
                   f"stationary={is_stationary}")
        
        return {
            'stationary': is_stationary,
            'p_value': p_value,
            'adf_statistic': adf_statistic,
            'critical_values': {k: v for k, v in critical_values.items()},
            'message': 'Stationary' if is_stationary else 'Non-stationary'
        }
    except Exception as e:
        logger.error(f"ADF test failed for {column_name}: {e}")
        return {
            'stationary': False,
            'p_value': 1.0,
            'adf_statistic': np.nan,
            'critical_values': {},
            'message': f'Test failed: {str(e)}'
        }

def ensure_stationarity(df: pd.DataFrame, column_name: str) -> Tuple[pd.Series, List[Dict[str, Any]]]:
    """
    Apply differencing until the series becomes stationary.
    
    Returns:
    - The stationary series
    - A list of test results for each differencing step
    """
    logger.info(f"Ensuring stationarity for column: {column_name}")
    
    series = df[column_name].copy()
    test_history = []
    max_diff = 5  # Safety limit to prevent infinite loops
    current_diff = 0
    
    while current_diff < max_diff:
        test_result = test_stationarity(series, column_name)
        test_history.append({
            'step': current_diff,
            'result': test_result
        })
        
        if test_result['stationary']:
            logger.info(f"Column {column_name} is stationary after {current_diff} differences")
            return series, test_history
        
        # Apply differencing
        series = series.diff().dropna()
        current_diff += 1
        
        if len(series) < 10:
            logger.error(f"Series for {column_name} became too short after differencing")
            break
    
    logger.warning(f"Could not achieve stationarity for {column_name} within {max_diff} differences")
    return series, test_history

def normalize_to_zscore(df: pd.DataFrame, column_name: str) -> pd.Series:
    """
    Normalize a column to z-scores (mean=0, std=1).
    """
    logger.info(f"Normalizing column {column_name} to z-scores")
    
    series = df[column_name].copy()
    mean = series.mean()
    std = series.std()
    
    if std == 0:
        logger.warning(f"Standard deviation is zero for {column_name}, cannot normalize")
        return series - mean  # Just center it
    
    z_scores = (series - mean) / std
    return z_scores

def validate_data_length(df: pd.DataFrame, min_length: int = 20) -> bool:
    """
    Check if the dataset has sufficient length for statistical analysis.
    """
    if len(df) < min_length:
        logger.error(f"Insufficient data for Granger causality: {len(df)} rows < {min_length} required")
        return False
    return True

def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save DataFrame to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved data to {filepath}")

def main():
    """
    Main preprocessing pipeline:
    1. Load raw GDELT and Google Trends data
    2. Align timestamps
    3. Test stationarity
    4. Apply differencing if needed
    5. Normalize to z-scores
    6. Save processed data
    """
    logger.info("Starting preprocessing pipeline")
    
    # File paths
    gdelt_file = os.path.join(RAW_DATA_DIR, "gdelt_events.csv")
    trends_file = os.path.join(RAW_DATA_DIR, "google_trends.csv")
    output_file = os.path.join(PROCESSED_DATA_DIR, "aligned_timeseries.csv")
    stationarity_file = os.path.join(PROCESSED_DATA_DIR, "stationarity_check.csv")
    
    # Check input files exist
    if not os.path.exists(gdelt_file) or not os.path.exists(trends_file):
        logger.error("Input files not found. Please run data fetching scripts first.")
        sys.exit(1)
    
    # Load data
    try:
        gdelt_df = load_gdelt_data(gdelt_file)
        trends_df = load_google_trends_data(trends_file)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # Align timestamps
    aligned_df = align_timestamps(gdelt_df, trends_df)
    
    # Validate data length
    if not validate_data_length(aligned_df):
        logger.error("Insufficient data for analysis")
        sys.exit(1)
    
    # Column names for processing
    gdelt_col = 'gdelt_event_count'
    trends_cols = ['trends_anticipatory_anxiety', 'trends_worry_about_future']
    
    # Ensure stationarity and collect results
    stationarity_results = []
    
    # Process GDELT data
    if gdelt_col in aligned_df.columns:
        stationary_gdelt, gdelt_history = ensure_stationarity(aligned_df, gdelt_col)
        stationarity_results.append({
            'column': gdelt_col,
            'final_stationary': stationary_gdelt.values,
            'history': gdelt_history
        })
        aligned_df[gdelt_col] = stationary_gdelt.values[:len(aligned_df)]
    
    # Process Trends data
    for col in trends_cols:
        if col in aligned_df.columns:
            stationary_trends, trends_history = ensure_stationarity(aligned_df, col)
            stationarity_results.append({
                'column': col,
                'final_stationary': stationary_trends.values,
                'history': trends_history
            })
            aligned_df[col] = stationary_trends.values[:len(aligned_df)]
    
    # Normalize to z-scores
    for col in [gdelt_col] + trends_cols:
        if col in aligned_df.columns:
            aligned_df[col] = normalize_to_zscore(aligned_df, col)
    
    # Save aligned timeseries
    save_to_csv(aligned_df, output_file)
    
    # Save stationarity check report
    stationarity_df = pd.DataFrame([{
        'column': r['column'],
        'is_stationary': r['history'][-1]['result']['stationary'] if r['history'] else False,
        'p_value': r['history'][-1]['result']['p_value'] if r['history'] else None,
        'differences_applied': len(r['history']) - 1 if r['history'] else 0,
        'message': r['history'][-1]['result']['message'] if r['history'] else 'No data'
    } for r in stationarity_results])
    
    save_to_csv(stationarity_df, stationarity_file)
    
    logger.info("Preprocessing pipeline completed successfully")
    return aligned_df

if __name__ == "__main__":
    main()