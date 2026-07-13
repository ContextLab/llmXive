import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from logger import get_logger, get_project_root

# Initialize logger
logger = get_logger(__name__)

def clean_traffic_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean traffic data ensuring 'traffic_volume' retains 0.0 values.
    Only imputation/exclusion applies to NaN values.
    Logs excluded rows to data/processed/exclusion_log.csv.
    """
    logger.info("Starting traffic data cleaning.")
    df_clean = df.copy()

    # Identify rows with NaN in traffic_volume
    nan_mask = df_clean['traffic_volume'].isna()
    nan_count = nan_mask.sum()

    if nan_count > 0:
        logger.warning(f"Found {nan_count} rows with NaN in 'traffic_volume'. Excluding them.")
        # Log excluded rows
        excluded_df = df_clean[nan_mask]
        log_path = get_project_root() / "data" / "processed" / "exclusion_log.csv"
        excluded_df.to_csv(log_path, index=False)
        
        # Drop NaN rows
        df_clean = df_clean.dropna(subset=['traffic_volume'])
    else:
        logger.info("No NaN values found in 'traffic_volume'.")

    logger.info(f"Traffic data cleaning complete. Rows remaining: {len(df_clean)}")
    return df_clean

def apply_iqr_filter(df: pd.DataFrame, column: str = 'noise_level_db', k: float = 1.5) -> pd.DataFrame:
    """
    Apply IQR filter (1.5x IQR) for decibel outlier removal.
    
    Args:
        df: Input DataFrame containing the noise column.
        column: Name of the column to filter (default: 'noise_level_db').
        k: Multiplier for IQR (default: 1.5).
        
    Returns:
        Filtered DataFrame with outliers removed.
    """
    logger.info(f"Applying IQR filter (k={k}) to column '{column}'.")
    
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame. Available columns: {df.columns.tolist()}")
    
    # Ensure numeric type
    series = pd.to_numeric(df[column], errors='coerce')
    
    # Calculate Q1, Q3, and IQR
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    
    logger.info(f"IQR Stats for {column}: Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f}")
    logger.info(f"Filter bounds: [{lower_bound:.2f}, {upper_bound:.2f}]")
    
    # Identify outliers
    outliers_mask = (series < lower_bound) | (series > upper_bound)
    outlier_count = outliers_mask.sum()
    total_count = len(series)
    
    if outlier_count > 0:
        logger.warning(f"Found {outlier_count} outliers ({100*outlier_count/total_count:.2f}%) in '{column}'. Removing them.")
        df_filtered = df[~outliers_mask].copy()
    else:
        logger.info(f"No outliers found in '{column}'.")
        df_filtered = df.copy()
        
    logger.info(f"IQR filtering complete. Rows remaining: {len(df_filtered)}")
    return df_filtered

def aggregate_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate noise metrics per day per grid cell.
    Unit of analysis is (grid_id, date).
    Calculates mean, median, and 95th percentile.
    
    Args:
        df: DataFrame with 'grid_id', 'date', and 'noise_level_db'.
        
    Returns:
        DataFrame with daily aggregated metrics.
    """
    logger.info("Starting daily aggregation.")
    
    required_cols = ['grid_id', 'date', 'noise_level_db']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns for aggregation: {missing}")
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Aggregate
    aggregated = df.groupby(['grid_id', 'date']).agg(
        noise_mean=('noise_level_db', 'mean'),
        noise_median=('noise_level_db', 'median'),
        noise_p95=('noise_level_db', lambda x: x.quantile(0.95))
    ).reset_index()
    
    logger.info(f"Daily aggregation complete. Output rows: {len(aggregated)}")
    return aggregated