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
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
GDELT_FILE = os.path.join(DATA_RAW_DIR, "gdelt_events.csv")
GOOGLE_TRENDS_FILE = os.path.join(DATA_RAW_DIR, "google_trends.csv")
OUTPUT_FILE = os.path.join(DATA_PROCESSED_DIR, "aligned_timeseries.csv")
STATIONARITY_CHECK_FILE = os.path.join(DATA_PROCESSED_DIR, "stationarity_check.csv")
VALIDATION_STATUS_FILE = os.path.join(DATA_PROCESSED_DIR, "validation_status.json")

MIN_SERIES_LENGTH = 20
ADF_THRESHOLD = 0.05


def load_gdelt_data(filepath: str) -> pd.DataFrame:
    """Load GDELT events data."""
    logger.info(f"Loading GDELT data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GDELT file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp'])
        df.drop(columns=['timestamp'], inplace=True)
    else:
        raise ValueError("GDELT data must have a 'date' or 'timestamp' column")
    return df


def load_google_trends_data(filepath: str) -> pd.DataFrame:
    """Load Google Trends data."""
    logger.info(f"Loading Google Trends data from {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Google Trends file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp'])
        df.drop(columns=['timestamp'], inplace=True)
    else:
        raise ValueError("Google Trends data must have a 'date' or 'timestamp' column")
    return df


def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align timestamps to daily intervals.
    Preserves zero-event days as valid zeros.
    Uses linear interpolation ONLY for null/missing values.
    """
    logger.info("Aligning timestamps to daily intervals...")

    # Determine common date range
    min_date = max(gdelt_df['date'].min(), trends_df['date'].min())
    max_date = min(gdelt_df['date'].max(), trends_df['date'].max())

    if min_date > max_date:
        raise ValueError("No overlapping date range between datasets")

    # Create complete daily date range
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='D')

    # Merge GDELT data
    gdelt_indexed = gdelt_df.set_index('date').reindex(full_date_range)
    gdelt_indexed = gdelt_indexed.rename(columns={'value': 'gdelt_events'})
    # Fill NaN in count columns with 0 (zero-event days are valid)
    if 'gdelt_events' in gdelt_indexed.columns:
        gdelt_indexed['gdelt_events'] = gdelt_indexed['gdelt_events'].fillna(0)

    # Merge Google Trends data
    trends_indexed = trends_df.set_index('date').reindex(full_date_range)
    trends_indexed = trends_indexed.rename(columns={'value': 'anxiety_index'})
    # Interpolate missing values in trends (linear interpolation)
    if 'anxiety_index' in trends_indexed.columns:
        trends_indexed['anxiety_index'] = trends_indexed['anxiety_index'].interpolate(method='linear')

    # Combine
    aligned_df = pd.concat([gdelt_indexed[['gdelt_events']], trends_indexed[['anxiety_index']]], axis=1)
    aligned_df.index.name = 'date'
    aligned_df = aligned_df.reset_index()

    logger.info(f"Aligned dataset shape: {aligned_df.shape}")
    return aligned_df


def test_stationarity(series: pd.Series, name: str = "Series") -> Tuple[bool, float, Dict]:
    """
    Perform Augmented Dickey-Fuller test for stationarity.
    Returns (is_stationary, p_value, result_dict)
    """
    result = adfuller(series.dropna(), autolag='AIC')
    p_value = result[1]
    is_stationary = p_value < ADF_THRESHOLD

    logger.info(f"{name} ADF Test: p-value = {p_value:.4f}, Stationary = {is_stationary}")

    details = {
        "statistic": result[0],
        "p_value": p_value,
        "critical_values": {k: v for k, v in result[4].items()},
        "is_stationary": is_stationary
    }
    return is_stationary, p_value, details


def ensure_stationarity(df: pd.DataFrame, col_name: str) -> Tuple[pd.Series, List[Dict], int]:
    """
    Apply differencing until the series is stationary (p < 0.05).
    Returns the stationary series, list of test results, and number of differences applied.
    """
    series = df[col_name].copy()
    test_results = []
    diff_count = 0
    max_diffs = 5  # Safety limit

    while diff_count < max_diffs:
        is_stationary, p_value, details = test_stationarity(series, f"{col_name} (diff {diff_count})")
        test_results.append(details)

        if is_stationary:
            break

        # Apply differencing
        series = series.diff().dropna()
        diff_count += 1

        if len(series) < 10:
            logger.warning(f"{col_name} series too short after {diff_count} differences")
            break

    if not is_stationary:
        logger.error(f"Failed to achieve stationarity for {col_name} after {diff_count} differences")

    return series, test_results, diff_count


def main():
    """Main preprocessing pipeline: alignment, stationarity check, differencing, and saving."""
    logger.info("Starting preprocessing pipeline (T018: Stationarity Testing)")

    try:
        # Load data
        gdelt_df = load_gdelt_data(GDELT_FILE)
        trends_df = load_google_trends_data(GOOGLE_TRENDS_FILE)

        # Align timestamps
        aligned_df = align_timestamps(gdelt_df, trends_df)

        # Check minimum length
        if len(aligned_df) < MIN_SERIES_LENGTH:
            error_msg = f"Insufficient data for Granger causality: {len(aligned_df)} rows < {MIN_SERIES_LENGTH}"
            logger.error(error_msg)
            with open(VALIDATION_STATUS_FILE, 'w') as f:
                json.dump({"status": "failed", "reason": error_msg}, f)
            sys.exit(1)

        # Ensure output directory exists
        os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

        # Process GDELT series
        gdelt_stationary, gdelt_results, gdelt_diffs = ensure_stationarity(aligned_df, 'gdelt_events')
        # Process Trends series
        trends_stationary, trends_results, trends_diffs = ensure_stationarity(aligned_df, 'anxiety_index')

        # Re-align indices after differencing (they might have different lengths now)
        min_len = min(len(gdelt_stationary), len(trends_stationary))
        gdelt_stationary = gdelt_stationary.iloc[:min_len]
        trends_stationary = trends_stationary.iloc[:min_len]

        # Create final processed dataframe
        processed_df = pd.DataFrame({
            'date': aligned_df['date'].iloc[-min_len:].values,
            'gdelt_events': gdelt_stationary.values,
            'anxiety_index': trends_stationary.values
        })

        # Save aligned, stationary data
        processed_df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved processed data to {OUTPUT_FILE}")

        # Save stationarity check results
        stationarity_data = []
        for i, res in enumerate(gdelt_results):
            stationarity_data.append({
                'series': 'gdelt_events',
                'diff_step': i,
                'p_value': res['p_value'],
                'is_stationary': res['is_stationary']
            })
        for i, res in enumerate(trends_results):
            stationarity_data.append({
                'series': 'anxiety_index',
                'diff_step': i,
                'p_value': res['p_value'],
                'is_stationary': res['is_stationary']
            })

        stationarity_df = pd.DataFrame(stationarity_data)
        stationarity_df.to_csv(STATIONARITY_CHECK_FILE, index=False)
        logger.info(f"Saved stationarity check to {STATIONARITY_CHECK_FILE}")

        # Update validation status
        validation_status = {
            "status": "success",
            "rows_processed": len(processed_df),
            "gdelt_diffs": gdelt_diffs,
            "trends_diffs": trends_diffs,
            "files": {
                "aligned": OUTPUT_FILE,
                "stationarity_check": STATIONARITY_CHECK_FILE
            }
        }
        with open(VALIDATION_STATUS_FILE, 'w') as f:
            json.dump(validation_status, f, indent=2)

        logger.info("Preprocessing pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        with open(VALIDATION_STATUS_FILE, 'w') as f:
            json.dump({"status": "failed", "reason": str(e)}, f)
        sys.exit(1)


if __name__ == "__main__":
    main()