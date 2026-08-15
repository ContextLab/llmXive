"""
Preprocessing module for aligning, stationarity-testing, and normalizing time-series data.
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
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution or different import paths
    import logging
    def get_logger(name: str):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_GDELT_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "gdelt_events.csv")
RAW_TRENDS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "google_trends.csv")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
ALIGNED_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "aligned_timeseries.csv")
STATIONARITY_OUTPUT_PATH = os.path.join(PROCESSED_DIR, "stationarity_check.csv")
VALIDATION_STATUS_PATH = os.path.join(PROCESSED_DIR, "validation_status.json")

def load_gdelt_data(filepath: str) -> pd.DataFrame:
    """Load and parse GDELT events data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"GDELT data file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.rename(columns={'Date': 'date'}, inplace=True)
    else:
        raise ValueError("GDELT data must contain a 'date' or 'Date' column")
    return df

def load_google_trends_data(filepath: str) -> pd.DataFrame:
    """Load and parse Google Trends data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Google Trends data file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.rename(columns={'Date': 'date'}, inplace=True)
    else:
        raise ValueError("Google Trends data must contain a 'date' or 'Date' column")
    return df

def align_timestamps(gdelt_df: pd.DataFrame, trends_df: pd.DataFrame) -> pd.DataFrame:
    """
    Align timestamps to daily resolution.
    Preserves zero-event days as valid zeros (does NOT interpolate zeros).
    Uses linear interpolation ONLY for null/missing values.
    """
    # Set date as index for both
    gdelt_df = gdelt_df.set_index('date')
    trends_df = trends_df.set_index('date')

    # Determine the intersection of date ranges
    start_date = max(gdelt_df.index.min(), trends_df.index.min())
    end_date = min(gdelt_df.index.max(), trends_df.index.max())

    if start_date > end_date:
        raise ValueError("No overlapping date range between GDELT and Trends data")

    # Create a complete daily date range for the intersection
    full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    # Reindex both dataframes to the full range
    gdelt_aligned = gdelt_df.reindex(full_date_range)
    trends_aligned = trends_df.reindex(full_date_range)

    # Identify which columns are numeric for interpolation
    # We assume the value column is named 'value' or 'count' or similar numeric type
    # For GDELT, typically 'count' or 'event_count'
    # For Trends, typically 'value'
    
    # Let's standardize column names for merging
    # GDELT: assume 'count' is the event count
    gdelt_val_col = 'count' if 'count' in gdelt_aligned.columns else \
                    'event_count' if 'event_count' in gdelt_aligned.columns else \
                    gdelt_aligned.select_dtypes(include=[np.number]).columns[0]
    
    # Trends: assume 'value' is the trend index
    trends_val_col = 'value' if 'value' in trends_aligned.columns else \
                     trends_aligned.select_dtypes(include=[np.number]).columns[0]

    # Rename for clarity in merge
    gdelt_aligned = gdelt_aligned.rename(columns={gdelt_val_col: 'gdelt_count'})
    trends_aligned = trends_aligned.rename(columns={trends_val_col: 'trends_value'})

    # Merge on index (date)
    merged = pd.merge(gdelt_aligned[['gdelt_count']], trends_aligned[['trends_value']], 
                      left_index=True, right_index=True, how='outer')

    # Reset index to have 'date' as a column
    merged.reset_index(inplace=True)
    merged.rename(columns={'index': 'date'}, inplace=True)

    # Handle missing values:
    # 1. For GDELT: If a date exists in the range but has no GDELT event, it's a 0.
    #    However, if the original data had NaN for some reason, we might need to fill.
    #    The task says: "preserve zero-event days as valid zeros (DO NOT interpolate zeros)".
    #    This implies we should fill NaNs in the GDELT column with 0, as absence of data in a 
    #    time-series of counts usually means 0 events.
    # 2. For Trends: We use linear interpolation for missing values.
    
    # Fill GDELT NaNs with 0 (assuming no record = 0 events)
    merged['gdelt_count'] = merged['gdelt_count'].fillna(0)
    
    # Linear interpolation for Trends
    merged['trends_value'] = merged['trends_value'].interpolate(method='linear')
    
    # If there are still NaNs at the edges (which interpolation can't fill), fill with nearest or drop?
    # For time series, usually drop or fill with edge value. Let's fill with nearest.
    merged['trends_value'] = merged['trends_value'].fillna(method='bfill').fillna(method='ffill')

    # Ensure date is datetime
    merged['date'] = pd.to_datetime(merged['date'])

    return merged

def test_stationarity(series: pd.Series) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Perform Augmented Dickey-Fuller (ADF) test for stationarity.
    Returns (is_stationary, p_value, stats_dict).
    """
    result = adfuller(series.dropna(), autolag='AIC')
    is_stationary = result[1] < 0.05
    return is_stationary, result[1], {
        'adf_statistic': result[0],
        'p_value': result[1],
        'critical_values': {k: v for k, v in result[4].items()}
    }

def ensure_stationarity(series: pd.Series, max_diff: int = 5) -> Tuple[pd.Series, List[int]]:
    """
    Apply differencing until the series is stationary or max_diff is reached.
    Returns the stationary series and a list of differencing orders applied.
    """
    current_series = series.copy()
    diff_orders = []
    
    for i in range(1, max_diff + 1):
        is_stationary, p_val, _ = test_stationarity(current_series)
        if is_stationary:
            break
        
        current_series = current_series.diff().dropna()
        diff_orders.append(i)
    
    # Final check
    is_stationary, p_val, _ = test_stationarity(current_series)
    if not is_stationary:
        logger.warning(f"Series did not become stationary after {max_diff} differences. p-value: {p_val}")
    
    return current_series, diff_orders

def normalize_to_zscore(series: pd.Series) -> pd.Series:
    """Convert series to z-scores (mean=0, std=1)."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        logger.warning("Standard deviation is zero. Cannot normalize to z-score.")
        return series
    return (series - mean) / std

def validate_data_length(series: pd.Series, min_length: int = 20) -> bool:
    """Check if the series has sufficient length for analysis."""
    if len(series) < min_length:
        logger.error(f"Insufficient data for Granger causality: {len(series)} < {min_length}")
        return False
    return True

def save_to_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save dataframe to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved data to {filepath}")

def main():
    """Main execution function for preprocessing and saving T020 artifacts."""
    logger.info("Starting preprocessing pipeline (T020)")
    
    # Ensure output directory exists
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # 1. Load Data
    try:
        gdelt_df = load_gdelt_data(RAW_GDELT_PATH)
        trends_df = load_google_trends_data(RAW_TRENDS_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Align Timestamps
    try:
        aligned_df = align_timestamps(gdelt_df, trends_df)
        logger.info(f"Aligned data shape: {aligned_df.shape}")
    except Exception as e:
        logger.error(f"Failed to align timestamps: {e}")
        sys.exit(1)

    # 3. Validate Data Length
    if not validate_data_length(aligned_df['gdelt_count']):
        sys.exit(1)
    if not validate_data_length(aligned_df['trends_value']):
        sys.exit(1)

    # 4. Stationarity Testing and Differencing
    stationarity_results = []
    processed_gdelt = aligned_df['gdelt_count']
    processed_trends = aligned_df['trends_value']
    
    # Test and process GDELT
    is_stat_gdelt, p_gdelt, stats_gdelt = test_stationarity(processed_gdelt)
    if not is_stat_gdelt:
        processed_gdelt, diff_gdelt = ensure_stationarity(processed_gdelt)
        logger.info(f"GDELT required {len(diff_gdelt)} differences to become stationary.")
    else:
        diff_gdelt = []
    
    # Test and process Trends
    is_stat_trends, p_trends, stats_trends = test_stationarity(processed_trends)
    if not is_stat_trends:
        processed_trends, diff_trends = ensure_stationarity(processed_trends)
        logger.info(f"Trends required {len(diff_trends)} differences to become stationary.")
    else:
        diff_trends = []

    # Record stationarity check results
    stationarity_results.append({
        'series': 'gdelt_count',
        'original_stationary': is_stat_gdelt,
        'original_p_value': p_gdelt,
        'differences_applied': len(diff_gdelt),
        'final_stationary': test_stationarity(processed_gdelt)[0],
        'final_p_value': test_stationarity(processed_gdelt)[1]
    })
    stationarity_results.append({
        'series': 'trends_value',
        'original_stationary': is_stat_trends,
        'original_p_value': p_trends,
        'differences_applied': len(diff_trends),
        'final_stationary': test_stationarity(processed_trends)[0],
        'final_p_value': test_stationarity(processed_trends)[1]
    })

    # 5. Normalization (Z-score)
    # Apply normalization AFTER stationarity is achieved
    normalized_gdelt = normalize_to_zscore(processed_gdelt)
    normalized_trends = normalize_to_zscore(processed_trends)

    # 6. Construct Final DataFrame
    # Re-align the processed series with the original date index
    final_df = pd.DataFrame({
        'date': aligned_df['date'].iloc[-len(normalized_gdelt):],
        'gdelt_zscore': normalized_gdelt.values,
        'trends_zscore': normalized_trends.values
    })
    
    # Ensure dates are aligned (in case differencing dropped rows)
    # The processed series are shorter than the original if differenced.
    # We need to match them with the corresponding dates.
    # Since we dropped NaNs from diff, the last N rows of the original aligned_df correspond to the processed series.
    # However, the index of processed_gdelt is the original index (minus dropped NaNs).
    # Let's reconstruct properly:
    final_dates = processed_gdelt.index if hasattr(processed_gdelt, 'index') else aligned_df['date'].iloc[-len(processed_gdelt):]
    
    final_df = pd.DataFrame({
        'date': pd.to_datetime(final_dates),
        'gdelt_zscore': normalized_gdelt.values,
        'trends_zscore': normalized_trends.values
    })
    
    # 7. Save Outputs
    save_to_csv(final_df, ALIGNED_OUTPUT_PATH)
    
    # Save stationarity check results
    stat_df = pd.DataFrame(stationarity_results)
    save_to_csv(stat_df, STATIONARITY_OUTPUT_PATH)

    # 8. Validation Status
    validation_status = {
        'task_id': 'T020',
        'timestamp': datetime.now().isoformat(),
        'status': 'completed',
        'outputs': {
            'aligned_timeseries': ALIGNED_OUTPUT_PATH,
            'stationarity_check': STATIONARITY_OUTPUT_PATH
        },
        'summary': {
            'rows_processed': len(final_df),
            'gdelt_stationary': stationarity_results[0]['final_stationary'],
            'trends_stationary': stationarity_results[1]['final_stationary']
        }
    }
    
    with open(VALIDATION_STATUS_PATH, 'w') as f:
        json.dump(validation_status, f, indent=2)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
