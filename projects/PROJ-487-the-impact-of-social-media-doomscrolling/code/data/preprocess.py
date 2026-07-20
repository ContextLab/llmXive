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

# Configuration constants
MIN_DATA_LENGTH = 20
DATA_DIR_RAW = "data/raw"
DATA_DIR_PROCESSED = "data/processed"
FILE_GDELT = os.path.join(DATA_DIR_RAW, "gdelt_events.csv")
FILE_TRENDS = os.path.join(DATA_DIR_RAW, "google_trends.csv")
FILE_OUTPUT = os.path.join(DATA_DIR_PROCESSED, "aligned_timeseries.csv")
FILE_STATIONARITY = os.path.join(DATA_DIR_PROCESSED, "stationarity_check.csv")
FILE_VALIDATION_STATUS = os.path.join(DATA_DIR_PROCESSED, "validation_status.json")

def load_gdelt_data(filepath: str = FILE_GDELT) -> pd.DataFrame:
    """Load GDELT events data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GDELT data file not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['date'])
    if 'date' not in df.columns or 'event_count' not in df.columns:
        raise ValueError(f"GDELT data missing required columns. Found: {df.columns.tolist()}")
    return df[['date', 'event_count']]

def load_google_trends_data(filepath: str = FILE_TRENDS) -> pd.DataFrame:
    """Load Google Trends data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Google Trends data file not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['date'])
    if 'date' not in df.columns or 'interest_score' not in df.columns:
        raise ValueError(f"Google Trends data missing required columns. Found: {df.columns.tolist()}")
    return df[['date', 'interest_score']]

def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """Align timestamps to daily intervals, preserving zero-event days."""
    # Get the intersection of date ranges
    min_date = max(gdelt_df['date'].min(), trends_df['date'].min())
    max_date = min(gdelt_df['date'].max(), trends_df['date'].max())

    if min_date > max_date:
        raise ValueError("No overlapping date range between datasets")

    # Create a complete daily date range
    full_range = pd.date_range(start=min_date, end=max_date, freq='D')
    aligned_df = pd.DataFrame({'date': full_range})

    # Merge GDELT data
    gdelt_df = gdelt_df.set_index('date')
    aligned_df = aligned_df.merge(gdelt_df, left_on='date', right_index=True, how='left')

    # Merge Trends data
    trends_df = trends_df.set_index('date')
    aligned_df = aligned_df.merge(trends_df, left_on='date', right_index=True, how='left')

    # Reset index
    aligned_df = aligned_df.reset_index(drop=True)

    # Interpolate ONLY null/missing values (NOT zeros)
    # Fill NaNs with linear interpolation
    aligned_df['event_count'] = aligned_df['event_count'].interpolate(method='linear')
    aligned_df['interest_score'] = aligned_df['interest_score'].interpolate(method='linear')

    # Fill any remaining edge NaNs (if interpolation failed at boundaries)
    aligned_df['event_count'] = aligned_df['event_count'].fillna(0)
    aligned_df['interest_score'] = aligned_df['interest_score'].fillna(0)

    return aligned_df

def test_stationarity(series: pd.Series, name: str = "series") -> Dict[str, Any]:
    """Perform Augmented Dickey-Fuller test for stationarity."""
    result = adfuller(series.dropna(), autolag='AIC')
    return {
        "name": name,
        "adf_statistic": result[0],
        "p_value": result[1],
        "critical_values": {k: v for k, v in result[4].items()},
        "is_stationary": result[1] < 0.05
    }

def ensure_stationarity(df: pd.DataFrame, col: str, max_diffs: int = 5) -> Tuple[pd.Series, int, Dict[str, Any]]:
    """Ensure series is stationary by differencing if necessary."""
    current_series = df[col].copy()
    diffs_applied = 0
    original_stats = test_stationarity(current_series, f"{col}_original")

    if original_stats['is_stationary']:
        return current_series, 0, original_stats

    for i in range(1, max_diffs + 1):
        current_series = current_series.diff().dropna()
        stats = test_stationarity(current_series, f"{col}_diff_{i}")
        diffs_applied = i
        if stats['is_stationary']:
            return current_series, diffs_applied, stats

    # If not stationary after max_diffs, return best effort
    return current_series, diffs_applied, stats

def normalize_to_zscore(series: pd.Series) -> pd.Series:
    """Convert series to z-scores (mean=0, std=1)."""
    mean_val = series.mean()
    std_val = series.std()
    if std_val == 0:
        logger.warning(f"Standard deviation is zero for series. Returning zeros.")
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - mean_val) / std_val

def validate_data_length(df: pd.DataFrame, min_length: int = MIN_DATA_LENGTH) -> bool:
    """
    Validate that the time-series has sufficient length for Granger causality.
    Returns True if length >= min_length, False otherwise.
    """
    length = len(df)
    if length < min_length:
        logger.error(f"Insufficient data for Granger causality: length={length} < {min_length}")
        return False
    return True

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting data preprocessing pipeline...")

    try:
        # Load data
        logger.info("Loading GDELT data...")
        gdelt_df = load_gdelt_data()
        logger.info(f"Loaded {len(gdelt_df)} GDELT records.")

        logger.info("Loading Google Trends data...")
        trends_df = load_google_trends_data()
        logger.info(f"Loaded {len(trends_df)} Trends records.")

        # Align timestamps
        logger.info("Aligning timestamps...")
        aligned_df = align_timestamps(gdelt_df, trends_df)
        logger.info(f"Aligned data has {len(aligned_df)} rows.")

        # --- T021: Validation for Granger Causality Length ---
        if not validate_data_length(aligned_df, MIN_DATA_LENGTH):
            logger.error("Validation failed: Insufficient data for Granger causality.")
            # Write failure status
            status = {
                "status": "failed",
                "reason": "Insufficient data for Granger causality",
                "data_length": len(aligned_df),
                "required_minimum": MIN_DATA_LENGTH,
                "timestamp": datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(FILE_VALIDATION_STATUS), exist_ok=True)
            with open(FILE_VALIDATION_STATUS, 'w') as f:
                json.dump(status, f, indent=2)
            sys.exit(1)
        # -----------------------------------------------------

        # Ensure stationarity
        logger.info("Testing and ensuring stationarity...")
        gdelt_stationary, gdelt_diffs, gdelt_stats = ensure_stationarity(aligned_df, 'event_count')
        trends_stationary, trends_diffs, trends_stats = ensure_stationarity(aligned_df, 'interest_score')

        logger.info(f"GDELT stationarity: p={gdelt_stats['p_value']:.4f}, diffs={gdelt_diffs}")
        logger.info(f"Trends stationarity: p={trends_stats['p_value']:.4f}, diffs={trends_diffs}")

        # Save stationarity check report
        stationarity_report = {
            "gdelt": gdelt_stats,
            "trends": trends_stats
        }
        os.makedirs(os.path.dirname(FILE_STATIONARITY), exist_ok=True)
        with open(FILE_STATIONARITY, 'w') as f:
            json.dump(stationarity_report, f, indent=2)
        logger.info(f"Stationarity check saved to {FILE_STATIONARITY}")

        # Re-align if differencing changed lengths (simplest approach: dropna on the differenced series)
        # Since ensure_stationarity returns a shorter series, we need to re-index or just take the common index
        # For simplicity in this pipeline, we assume the differenced series are aligned by index if we processed them on the same df
        # However, diff() drops the first row. If both dropped rows, they are aligned.
        # If one dropped more (unlikely with max_diffs loop logic), we align again.
        min_len = min(len(gdelt_stationary), len(trends_stationary))
        final_gdelt = gdelt_stationary.iloc[-min_len:]
        final_trends = trends_stationary.iloc[-min_len:]

        # Normalize to z-scores
        logger.info("Normalizing data to z-scores...")
        final_gdelt_norm = normalize_to_zscore(final_gdelt)
        final_trends_norm = normalize_to_zscore(final_trends)

        # Construct final output dataframe
        # We need to align the dates from the original aligned_df corresponding to the final rows
        # Since we took the last min_len rows, we take the last min_len dates
        final_dates = aligned_df['date'].iloc[-min_len:].reset_index(drop=True)

        final_df = pd.DataFrame({
            'date': final_dates,
            'gdelt_zscore': final_gdelt_norm.values,
            'trends_zscore': final_trends_norm.values
        })

        # Save processed data
        os.makedirs(os.path.dirname(FILE_OUTPUT), exist_ok=True)
        final_df.to_csv(FILE_OUTPUT, index=False)
        logger.info(f"Processed data saved to {FILE_OUTPUT}")

        # Write success status
        status = {
            "status": "success",
            "data_length": len(final_df),
            "gdelt_stationarity": gdelt_stats['is_stationary'],
            "trends_stationarity": trends_stats['is_stationary'],
            "timestamp": datetime.now().isoformat()
        }
        with open(FILE_VALIDATION_STATUS, 'w') as f:
            json.dump(status, f, indent=2)

        logger.info("Preprocessing pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}", exc_info=True)
        status = {
            "status": "failed",
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(FILE_VALIDATION_STATUS), exist_ok=True)
        with open(FILE_VALIDATION_STATUS, 'w') as f:
            json.dump(status, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()