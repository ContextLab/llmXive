"""
Preprocessing module for sentiment drift analysis.

Handles data loading, resampling, interpolation, missing data flagging,
and noise reduction via rolling averages.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

def load_raw_data() -> Dict[str, pd.DataFrame]:
    """
    Load raw data files from the data/raw directory.
    
    Returns:
        Dict mapping variable names to DataFrames.
    """
    data_files = {
        'gdelt_sentiment': 'gdelt_sentiment.csv',
        'fred_gdp': 'fred_gdp.csv',
        'fred_unrate': 'fred_unrate.csv'
    }
    
    raw_data = {}
    for name, filename in data_files.items():
        filepath = RAW_DATA_DIR / filename
        if not filepath.exists():
            logger.warning(f"Raw data file not found: {filepath}")
            continue
        
        try:
            df = pd.read_csv(filepath, parse_dates=['date'])
            raw_data[name] = df
            logger.info(f"Loaded {filename}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            
    return raw_data

def resample_sentiment_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample daily sentiment data to monthly averages.
    
    Args:
        df: DataFrame with 'date' column and sentiment scores.
        
    Returns:
        Monthly averaged DataFrame.
    """
    if 'date' not in df.columns:
        raise ValueError("DataFrame must contain 'date' column")
        
    df = df.set_index('date')
    
    # Resample to monthly mean
    monthly_df = df.resample('ME').mean()
    
    # Reset index for consistency
    monthly_df = monthly_df.reset_index()
    
    logger.info(f"Resampled sentiment to monthly: {len(monthly_df)} rows")
    return monthly_df

def resample_macro_to_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample quarterly macro data to monthly using forward-fill.
    
    Args:
        df: DataFrame with 'date' column and macro variables.
        
    Returns:
        Monthly DataFrame with forward-filled values.
    """
    if 'date' not in df.columns:
        raise ValueError("DataFrame must contain 'date' column")
        
    df = df.set_index('date')
    
    # Resample to monthly with forward-fill
    monthly_df = df.resample('ME').ffill()
    
    # Reset index
    monthly_df = monthly_df.reset_index()
    
    logger.info(f"Resampled macro to monthly: {len(monthly_df)} rows")
    return monthly_df

def interpolate_missing(df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
    """
    Interpolate missing values in the DataFrame.
    
    Args:
        df: DataFrame with potential missing values.
        method: Interpolation method ('linear', 'forward_fill', 'backward_fill').
        
    Returns:
        DataFrame with interpolated values.
    """
    if method == 'linear':
        df = df.interpolate(method='linear')
    elif method == 'forward_fill':
        df = df.ffill()
    elif method == 'backward_fill':
        df = df.bfill()
    else:
        raise ValueError(f"Unknown interpolation method: {method}")
        
    return df

def calculate_missing_rate(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the missing data rate for each column.
    
    Args:
        df: DataFrame to analyze.
        
    Returns:
        Dict mapping column names to missing rates (0.0 to 1.0).
    """
    missing_rates = {}
    for col in df.columns:
        if col == 'date':
            continue
        missing_count = df[col].isna().sum()
        total_count = len(df)
        missing_rates[col] = missing_count / total_count if total_count > 0 else 0.0
        
    return missing_rates

def flag_low_confidence(df: pd.DataFrame, confidence_threshold: float = 0.7, min_samples: int = 100) -> pd.DataFrame:
    """
    Flag periods with low confidence or insufficient sample size.
    
    Args:
        df: DataFrame with sentiment data.
        confidence_threshold: Minimum confidence score.
        min_samples: Minimum number of samples required.
        
    Returns:
        DataFrame with 'low_confidence' flag column.
    """
    df['low_confidence'] = False
    
    # Flag based on confidence threshold if column exists
    if 'confidence' in df.columns:
        df.loc[df['confidence'] < confidence_threshold, 'low_confidence'] = True
        
    # Flag based on sample size if column exists
    if 'sample_size' in df.columns:
        df.loc[df['sample_size'] < min_samples, 'low_confidence'] = True
        
    return df

def apply_rolling_average(df: pd.DataFrame, window: int = 3, column: str = 'sentiment_score') -> pd.DataFrame:
    """
    Apply rolling average to reduce noise in sentiment data.
    
    Args:
        df: DataFrame containing the time series.
        window: Window size for rolling average (in months).
        column: Name of the column to smooth.
        
    Returns:
        DataFrame with a new column '<column>_smoothed' containing the rolling average.
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame. Available columns: {list(df.columns)}")
        return df
        
    # Apply rolling average
    smoothed_col = f"{column}_smoothed"
    df[smoothed_col] = df[column].rolling(window=window, min_periods=1).mean()
    
    logger.info(f"Applied {window}-month rolling average to '{column}', created '{smoothed_col}'")
    return df

def run_adf_test(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """
    Run Augmented Dickey-Fuller test for stationarity.
    
    Args:
        df: DataFrame with time series data.
        column: Column name to test.
        
    Returns:
        Dict with test statistics.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
        
    series = df[column].dropna()
    result = adfuller(series)
    
    return {
        'adf_statistic': result[0],
        'p_value': result[1],
        'critical_values': {k: v for k, v in result[4].items()},
        'is_stationary': result[1] < 0.05
    }

def align_and_preprocess(raw_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Align all data sources to monthly frequency and preprocess.
    
    Args:
        raw_data: Dict of raw DataFrames.
        
    Returns:
        Aligned and preprocessed DataFrame.
    """
    if 'gdelt_sentiment' not in raw_data:
        raise ValueError("Missing gdelt_sentiment data")
        
    # Resample sentiment to monthly
    sentiment_monthly = resample_sentiment_to_monthly(raw_data['gdelt_sentiment'])
    
    # Resample macro data to monthly
    macro_data = {}
    for key in ['fred_gdp', 'fred_unrate']:
        if key in raw_data:
            macro_data[key] = resample_macro_to_monthly(raw_data[key])
    
    # Merge sentiment with macro data
    merged_df = sentiment_monthly
    for key, df in macro_data.items():
        # Extract relevant columns
        if key == 'fred_gdp':
            cols_to_keep = ['date', 'gdp'] if 'gdp' in df.columns else ['date']
            merged_df = merged_df.merge(df[cols_to_keep], on='date', how='left')
        elif key == 'fred_unrate':
            cols_to_keep = ['date', 'unrate'] if 'unrate' in df.columns else ['date']
            merged_df = merged_df.merge(df[cols_to_keep], on='date', how='left')
    
    # Sort by date
    merged_df = merged_df.sort_values('date').reset_index(drop=True)
    
    # Interpolate missing values
    merged_df = interpolate_missing(merged_df, method='linear')
    
    # Calculate missing rate
    missing_rates = calculate_missing_rate(merged_df)
    logger.info(f"Missing rates: {missing_rates}")
    
    # Check if any variable exceeds 5% missing rate
    high_missing = {k: v for k, v in missing_rates.items() if v > 0.05}
    if high_missing:
        logger.warning(f"Variables with >5% missing data: {high_missing}")
        # Flag these periods (could add a column if needed)
    
    # Apply rolling average for noise reduction
    if 'sentiment_score' in merged_df.columns:
        merged_df = apply_rolling_average(merged_df, window=3, column='sentiment_score')
        
    return merged_df

def save_outputs(df: pd.DataFrame, output_path: Path, log_path: Path, missing_rates: Dict[str, float]):
    """
    Save processed data and quality log.
    
    Args:
        df: Processed DataFrame.
        output_path: Path for CSV output.
        log_path: Path for JSON log.
        missing_rates: Dict of missing rates.
    """
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
    
    # Save quality log
    quality_log = {
        'timestamp': datetime.now().isoformat(),
        'missing_rates': missing_rates,
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': list(df.columns)
    }
    
    with open(log_path, 'w') as f:
        json.dump(quality_log, f, indent=2)
    logger.info(f"Saved quality log to {log_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")
    
    # Load raw data
    raw_data = load_raw_data()
    
    if not raw_data:
        logger.error("No raw data found. Exiting.")
        return
    
    # Align and preprocess
    processed_df = align_and_preprocess(raw_data)
    
    # Calculate missing rates for logging
    missing_rates = calculate_missing_rate(processed_df)
    
    # Define output paths
    output_path = PROCESSED_DATA_DIR / "aligned_monthly.csv"
    log_path = PROCESSED_DATA_DIR / "data_quality_log.json"
    
    # Save outputs
    save_outputs(processed_df, output_path, log_path, missing_rates)
    
    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()