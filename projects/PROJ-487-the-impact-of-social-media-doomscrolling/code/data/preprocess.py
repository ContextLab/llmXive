"""
Preprocessing Logic for Time Series Data (T019)

Implements ADF test, differencing loop, and z-score normalization.
Reads from data/raw/gdelt_events.csv and data/raw/google_trends.csv (aligned by T018).
Saves to data/processed/aligned_timeseries.csv and data/processed/stationarity_check.csv.
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

# Import logging utility
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
MAX_DIFF_ITERATIONS = 5
COMPLETENESS_THRESHOLD = 0.95
MIN_ROWS = 20
ADF_THRESHOLD = 0.05

def load_gdelt_data(filepath: str) -> pd.DataFrame:
    """Load GDELT data from CSV."""
    if not os.path.exists(filepath):
        logger.error(f"GDELT data file not found: {filepath}")
        sys.exit(1)
    df = pd.read_csv(filepath, parse_dates=['date'])
    if 'date' in df.columns:
        df = df.set_index('date')
    return df

def load_google_trends_data(filepath: str) -> pd.DataFrame:
    """Load Google Trends data from CSV."""
    if not os.path.exists(filepath):
        logger.error(f"Google Trends data file not found: {filepath}")
        sys.exit(1)
    df = pd.read_csv(filepath, parse_dates=['date'])
    if 'date' in df.columns:
        df = df.set_index('date')
    return df

def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align timestamps to the intersection of both datasets.
    Assumes T018 has already handled interpolation and zero preservation.
    This function ensures the final index is the intersection.
    """
    # Ensure indices are datetime
    if not isinstance(gdelt_df.index, pd.DatetimeIndex):
        gdelt_df.index = pd.to_datetime(gdelt_df.index)
    if not isinstance(trends_df.index, pd.DatetimeIndex):
        trends_df.index = pd.to_datetime(trends_df.index)

    # Find intersection
    common_index = gdelt_df.index.intersection(trends_df.index)
    logger.info(f"Aligning timestamps. Intersection size: {len(common_index)}")

    # Reindex both to common index
    aligned_gdelt = gdelt_df.reindex(common_index)
    aligned_trends = trends_df.reindex(common_index)

    # Merge
    merged = pd.concat([aligned_gdelt, aligned_trends], axis=1)
    merged.columns = ['gdelt_value', 'trends_value'] # Standardize column names

    # Drop any rows that might have become NaN due to index mismatch (should be rare if intersection is used)
    merged = merged.dropna()

    return merged

def test_stationarity(series: pd.Series) -> Tuple[float, float, str]:
    """
    Run ADF test on a series.
    Returns (statistic, p-value, status_string).
    """
    try:
        result = adfuller(series.dropna(), autolag='AIC')
        p_value = result[1]
        status = "Stationary" if p_value < ADF_THRESHOLD else "Non-Stationary"
        return result[0], p_value, status
    except Exception as e:
        logger.error(f"ADF test failed: {e}")
        return np.nan, np.nan, "Error"

def ensure_stationarity(series: pd.Series, max_diff: int = MAX_DIFF_ITERATIONS) -> Tuple[pd.Series, List[Dict[str, Any]]]:
    """
    Difference the series until it is stationary or max_diff reached.
    Returns the stationary series and a log of the process.
    """
    log = []
    current_series = series.copy()
    diff_count = 0
    original_name = series.name

    # Initial check
    stat, p, status = test_stationarity(current_series)
    log.append({
        "step": "initial",
        "differences": 0,
        "adf_statistic": stat,
        "p_value": p,
        "status": status
    })

    while status == "Non-Stationary" and diff_count < max_diff:
        diff_count += 1
        logger.info(f"Differencing series (diff={diff_count})...")
        current_series = current_series.diff().dropna()

        if len(current_series) == 0:
            logger.error("Series became empty after differencing.")
            raise ValueError("Series became empty after differencing.")

        stat, p, status = test_stationarity(current_series)
        log.append({
            "step": f"diff_{diff_count}",
            "differences": diff_count,
            "adf_statistic": stat,
            "p_value": p,
            "status": status
        })

    if status == "Non-Stationary":
        raise RuntimeError(f"Series remains non-stationary after {max_diff} differences. Final p-value: {p}")

    current_series.name = f"{original_name}_diff{diff_count}" if diff_count > 0 else original_name
    return current_series, log

def normalize_to_zscore(series: pd.Series) -> pd.Series:
    """Apply z-score normalization."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        logger.warning(f"Standard deviation is zero for {series.name}. Returning zeros.")
        return pd.Series(0.0, index=series.index, name=series.name)
    return (series - mean) / std

def validate_data_length(series: pd.Series, min_rows: int = MIN_ROWS) -> bool:
    """Check if series has enough rows."""
    if len(series) < min_rows:
        logger.error(f"Data length {len(series)} is less than minimum required {min_rows}.")
        return False
    return True

def calculate_completeness(series: pd.Series) -> float:
    """Calculate percentage of non-null values."""
    total = len(series)
    valid = series.notna().sum()
    if total == 0:
        return 0.0
    return valid / total

def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save DataFrame to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath)
    logger.info(f"Saved data to {filepath}")

def main():
    """Main execution flow for T019."""
    logger.info("Starting Preprocessing Logic (T019)...")

    # Paths
    # Assuming T018 has produced aligned data, but T019 description says "Read from ... and ..."
    # T018 description: "Read from data/raw/gdelt_events.csv and data/raw/google_trends.csv"
    # T019 description: "Implement ADF test... Save to data/processed/aligned_timeseries.csv"
    # We assume T018 output is in data/processed/aligned_timeseries.csv?
    # Wait, T018 says "Save to data/processed/aligned_timeseries.csv" is NOT in T018 description.
    # T018 says: "interpolate... Read from data/raw/...". It does not explicitly say it saves.
    # However, T019 depends on T018.
    # Let's assume T018 saves to a temporary or intermediate file, or we re-align here.
    # Looking at T018 description again: "Implement timestamp alignment... Read from data/raw/...".
    # It does not specify output path.
    # T019 says: "Save to data/processed/aligned_timeseries.csv".
    # To be safe and robust, we will perform the alignment logic here if the file doesn't exist,
    # or read from the raw files and align them here, effectively combining T018 and T019 logic
    # if T018 didn't save.
    # BUT, the API surface for T018 (preprocess.py) already has `align_timestamps`.
    # If T018 was run, it might have saved to a temp file or we need to call it.
    # Let's assume the standard flow: T018 prepares the data, T019 processes it.
    # If T018 didn't save, we must do it.
    # Given the dependency, we will check for an intermediate aligned file or re-align.
    # For this implementation, we will assume the input is the raw files and we perform
    # alignment (T018 step) then stationarity (T019 step) in one go if needed,
    # OR we assume T018 saved to `data/processed/aligned_timeseries.csv`?
    # T019 says: "Save to data/processed/aligned_timeseries.csv". This implies it's the output of T019.
    # So T018 likely saved to a temp location or we re-do alignment.
    # Let's read from raw files and align here to ensure we have the data.

    gdelt_path = "data/raw/gdelt_events.csv"
    trends_path = "data/raw/google_trends.csv"
    output_aligned_path = "data/processed/aligned_timeseries.csv"
    output_stationarity_path = "data/processed/stationarity_check.csv"

    # Load data
    logger.info(f"Loading GDELT data from {gdelt_path}")
    gdelt_df = load_gdelt_data(gdelt_path)
    logger.info(f"Loading Google Trends data from {trends_path}")
    trends_df = load_google_trends_data(trends_path)

    # Align (T018 logic included here to ensure data is ready)
    # We assume the raw files have 'date' and 'value' columns.
    # We need to merge them.
    # T018 logic: align_timestamps(gdelt_df, trends_df)
    # We assume the raw files have been cleaned by T018 (interpolation done).
    # If T018 didn't save, we do it here.
    # Let's assume the raw files are ready (interpolated) as per T018 completion.
    # We just align the indices.

    aligned_df = align_timestamps(gdelt_df, trends_df)

    # Completeness Check (>= 95%)
    completeness = calculate_completeness(aligned_df['gdelt_value'])
    if completeness < COMPLETENESS_THRESHOLD:
        logger.error(f"Data completeness {completeness:.2%} is below threshold {COMPLETENESS_THRESHOLD:.2%}.")
        sys.exit(1)
    logger.info(f"Data completeness check passed: {completeness:.2%}")

    # Length Check (>= 20)
    if not validate_data_length(aligned_df['gdelt_value']):
        sys.exit(1)
    logger.info(f"Data length check passed: {len(aligned_df)} rows")

    # Save aligned data (T019 output requirement)
    save_to_csv(aligned_df, output_aligned_path)

    # Stationarity Processing
    stationarity_log = []
    processed_data = pd.DataFrame(index=aligned_df.index)

    for col in aligned_df.columns:
        logger.info(f"Processing stationarity for {col}...")
        try:
            stationary_series, log = ensure_stationarity(aligned_df[col])
            processed_data[col] = stationary_series
            stationarity_log.extend(log)
        except Exception as e:
            logger.error(f"Failed to ensure stationarity for {col}: {e}")
            sys.exit(1)

    # Z-Score Normalization
    logger.info("Applying Z-Score Normalization...")
    for col in processed_data.columns:
        processed_data[col] = normalize_to_zscore(processed_data[col])

    # Save processed aligned data (overwriting or new file? T019 says "Save to data/processed/aligned_timeseries.csv")
    # We overwrite the aligned file with the processed (stationary + normalized) data?
    # Or do we save the normalized version to the same path?
    # "Save to data/processed/aligned_timeseries.csv" usually implies the final output.
    # But we also need to save the stationarity check.
    # Let's save the normalized data to aligned_timeseries.csv.
    save_to_csv(processed_data, output_aligned_path)

    # Save Stationarity Check
    stationarity_df = pd.DataFrame(stationarity_log)
    save_to_csv(stationarity_df, output_stationarity_path)

    logger.info("Preprocessing Logic (T019) completed successfully.")

if __name__ == "__main__":
    main()