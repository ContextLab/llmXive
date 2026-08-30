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

# Import logging utility
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def load_gdelt_data(filepath: str) -> pd.DataFrame:
    """Load GDELT events data from CSV."""
    logger.info(f"Loading GDELT data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GDELT data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.rename(columns={'Date': 'date'})
    
    return df


def load_google_trends_data(filepath: str) -> pd.DataFrame:
    """Load Google Trends data from CSV."""
    logger.info(f"Loading Google Trends data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Google Trends data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.rename(columns={'Date': 'date'})
    
    return df


def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align both datasets to daily intervals using intersection of timestamps.
    Preserves zero-event days as valid zeros (does NOT interpolate zeros).
    
    Returns a DataFrame with aligned timestamps and columns from both sources.
    """
    logger.info("Aligning timestamps between GDELT and Google Trends data")
    
    # Ensure 'date' is the index for alignment
    gdelt_df = gdelt_df.set_index('date')
    trends_df = trends_df.set_index('date')
    
    # Find intersection of dates
    common_dates = gdelt_df.index.intersection(trends_df.index)
    
    if len(common_dates) == 0:
        raise ValueError("No common dates found between GDELT and Google Trends datasets")
    
    logger.info(f"Found {len(common_dates)} common dates for alignment")
    
    # Filter to common dates
    aligned_gdelt = gdelt_df.loc[common_dates]
    aligned_trends = trends_df.loc[common_dates]
    
    # Merge on index
    aligned_df = pd.merge(
        aligned_gdelt, 
        aligned_trends, 
        left_index=True, 
        right_index=True, 
        how='inner'
    )
    
    # Reset index to have 'date' as a column again
    aligned_df = aligned_df.reset_index()
    
    logger.info(f"Aligned dataset shape: {aligned_df.shape}")
    
    return aligned_df


def interpolate_missing_values(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Interpolate missing values (NaN) using linear interpolation.
    CRITICAL: Zero-event counts (value == 0.0) are preserved and NOT interpolated.
    
    This implements Spec FR-002 (linear interpolation) superseding Plan's forward-fill.
    """
    logger.info("Interpolating missing values (preserving zero-event days)")
    
    df_copy = df.copy()
    
    # Identify numeric columns (excluding the date column)
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns.tolist()
    
    # Store original zero values to ensure they are preserved
    zero_mask = {}
    for col in numeric_cols:
        zero_mask[col] = df_copy[col] == 0.0
    
    # Apply linear interpolation ONLY to NaN values
    # pandas.interpolate() by default only interpolates NaNs, not zeros
    df_copy[numeric_cols] = df_copy[numeric_cols].interpolate(method='linear')
    
    # Verify and ensure zero-event days remain zero (in case interpolation affected them)
    # This is a safety check to strictly enforce the requirement
    for col in numeric_cols:
        # Restore zeros where they existed originally
        df_copy.loc[zero_mask[col], col] = 0.0
    
    # Log verification
    for col in numeric_cols:
        original_zeros = zero_mask[col].sum()
        current_zeros = (df_copy[col] == 0.0).sum()
        logger.debug(f"Column {col}: Original zeros={original_zeros}, Current zeros={current_zeros}")
    
    logger.info("Interpolation complete. Zero-event days preserved.")
    
    return df_copy


def test_stationarity(series: pd.Series, name: str = "series") -> Tuple[bool, float]:
    """
    Perform Augmented Dickey-Fuller (ADF) test for stationarity.
    
    Returns:
        Tuple of (is_stationary, p_value)
    """
    logger.info(f"Testing stationarity for {name} using ADF test")
    
    try:
        result = adfuller(series.dropna(), autolag='AIC')
        p_value = result[1]
        is_stationary = p_value < 0.05
        
        logger.info(f"{name} ADF test: p-value={p_value:.6f}, Stationary={is_stationary}")
        
        return is_stationary, p_value
    except Exception as e:
        logger.error(f"ADF test failed for {name}: {e}")
        raise


def ensure_stationarity(df: pd.DataFrame, date_col: str = 'date') -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Ensure time series are stationary by applying differencing if needed.
    Iteratively differ until p-value < 0.05.
    
    Returns:
        Tuple of (differenced_df, dict of differences applied per column)
    """
    logger.info("Ensuring stationarity for all time series columns")
    
    df_copy = df.copy()
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns.tolist()
    diff_counts = {}
    
    for col in numeric_cols:
        series = df_copy[col]
        is_stationary, p_value = test_stationarity(series, col)
        
        diff_count = 0
        while not is_stationary:
            logger.info(f"{col} is non-stationary (p={p_value:.4f}). Applying differencing...")
            df_copy[col] = np.diff(df_copy[col].values, n=1)
            # Pad with NaN to maintain length
            df_copy[col] = pd.Series(df_copy[col].values, index=df_copy.index)
            df_copy.iloc[0, df_copy.columns.get_loc(col)] = np.nan
            
            diff_count += 1
            series = df_copy[col]
            is_stationary, p_value = test_stationarity(series, col)
            
            if diff_count > 5:
                logger.warning(f"Maximum differencing iterations reached for {col}. May still be non-stationary.")
                break
        
        diff_counts[col] = diff_count
        logger.info(f"{col} stationarity achieved after {diff_count} difference(s). Final p-value: {p_value:.6f}")
    
    # Drop rows with NaN created by differencing
    df_copy = df_copy.dropna()
    
    logger.info(f"Stationarity ensured. Differences applied: {diff_counts}")
    
    return df_copy, diff_counts


def normalize_to_zscore(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Normalize time series to z-scores (mean=0, std=1) using StandardScaler.
    """
    logger.info("Normalizing time series to z-scores")
    
    df_copy = df.copy()
    numeric_cols = df_copy.select_dtypes(include=[np.number]).columns.tolist()
    
    scaler = StandardScaler()
    df_copy[numeric_cols] = scaler.fit_transform(df_copy[numeric_cols])
    
    logger.info("Normalization complete. Data converted to z-scores.")
    
    return df_copy


def validate_data_length(df: pd.DataFrame, min_length: int = 20) -> bool:
    """
    Validate that the time series has sufficient length for Granger causality.
    
    Returns:
        True if length >= min_length, else raises error.
    """
    length = len(df)
    if length < min_length:
        error_msg = f"Insufficient data for Granger causality: {length} rows < {min_length} required"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Data length validation passed: {length} rows >= {min_length}")
    return True


def check_post_interpolation_completeness(df: pd.DataFrame, threshold: float = 0.95) -> Dict[str, Any]:
    """
    T022: Implement Post-Interpolation Completeness Check.
    
    1. Calculate completeness percentage: (count of non-null values / total rows) * 100.
    2. Verify completeness >= 95% (0.95).
    3. Return result dict with 'completeness_pct' if passed, or raise error if failed.
    
    Args:
        df: DataFrame to check (after interpolation)
        threshold: Minimum completeness threshold (default 0.95 = 95%)
    
    Returns:
        Dict with 'completeness_pct' and 'passed' status.
    
    Raises:
        ValueError: If completeness is below threshold.
    """
    logger.info("Performing post-interpolation completeness check")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        raise ValueError("No numeric columns found for completeness check")
    
    total_cells = len(df) * len(numeric_cols)
    non_null_cells = df[numeric_cols].notna().sum().sum()
    
    completeness_pct = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0.0
    
    logger.info(f"Post-interpolation completeness: {completeness_pct:.2f}%")
    
    result = {
        'completeness_pct': completeness_pct,
        'total_cells': total_cells,
        'non_null_cells': non_null_cells,
        'passed': completeness_pct >= (threshold * 100)
    }
    
    if not result['passed']:
        error_msg = f"Post-interpolation completeness check FAILED: {completeness_pct:.2f}% < {threshold*100:.2f}% threshold"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Post-interpolation completeness check PASSED: {completeness_pct:.2f}% >= {threshold*100:.2f}%")
    
    return result


def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save DataFrame to CSV."""
    logger.info(f"Saving data to {filepath}")
    df.to_csv(filepath, index=False)
    logger.info(f"Data saved successfully to {filepath}")


def main():
    """
    Main preprocessing pipeline execution.
    
    Executes the following steps:
    1. Load GDELT and Google Trends data
    2. Align timestamps
    3. Interpolate missing values (preserving zeros)
    4. Validate data length
    5. Ensure stationarity (ADF + differencing)
    6. Normalize to z-scores
    7. Perform post-interpolation completeness check (T022)
    8. Save processed outputs
    """
    logger.info("Starting preprocessing pipeline")
    
    # Paths
    gdelt_path = os.path.join("data", "raw", "gdelt_events.csv")
    trends_path = os.path.join("data", "raw", "google_trends.csv")
    aligned_path = os.path.join("data", "processed", "aligned_raw.csv")
    interpolated_path = os.path.join("data", "processed", "aligned_interpolated.csv")
    stationary_path = os.path.join("data", "processed", "aligned_timeseries.csv")
    stationarity_check_path = os.path.join("data", "processed", "stationarity_check.csv")
    validation_status_path = os.path.join("data", "processed", "validation_status.json")
    
    try:
        # 1. Load data
        gdelt_df = load_gdelt_data(gdelt_path)
        trends_df = load_google_trends_data(trends_path)
        
        # 2. Align timestamps
        aligned_df = align_timestamps(gdelt_df, trends_df)
        save_to_csv(aligned_df, aligned_path)
        
        # 3. Interpolate missing values
        interpolated_df = interpolate_missing_values(aligned_df)
        save_to_csv(interpolated_df, interpolated_path)
        
        # 4. T022: Post-Interpolation Completeness Check
        completeness_result = check_post_interpolation_completeness(interpolated_df, threshold=0.95)
        
        # Save validation status
        with open(validation_status_path, 'w') as f:
            json.dump(completeness_result, f, indent=2)
        logger.info(f"Validation status saved to {validation_status_path}")
        
        # 5. Validate data length
        validate_data_length(interpolated_df, min_length=20)
        
        # 6. Ensure stationarity
        stationary_df, diff_counts = ensure_stationarity(interpolated_df)
        
        # Save stationarity check info
        stationarity_info = {
            'differences_applied': diff_counts,
            'final_length': len(stationary_df)
        }
        with open(stationarity_check_path, 'w') as f:
            json.dump(stationarity_info, f, indent=2)
        
        # 7. Normalize to z-scores
        normalized_df = normalize_to_zscore(stationary_df)
        
        # 8. Save final outputs
        save_to_csv(normalized_df, stationary_path)
        
        logger.info("Preprocessing pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()