import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import get_project_root, get_data_processed_path

logger = get_logger(__name__)

def simple_average(df: pd.DataFrame, date_col: str = 'date', value_col: str = 'vote_share', bin_col: str = 'week_bin') -> pd.DataFrame:
    """
    Calculate arithmetic mean of vote shares per weekly bin (FR-003).
    
    Args:
        df: Input DataFrame with columns for date, vote_share, and week_bin.
        date_col: Name of the date column.
        value_col: Name of the vote share column.
        bin_col: Name of the weekly bin column.
        
    Returns:
        DataFrame with columns: week_bin, simple_avg_forecast, count
    """
    if df.empty:
        logger.warning("Input DataFrame is empty for simple_average.")
        return pd.DataFrame(columns=[bin_col, 'simple_avg_forecast', 'count'])

    result = df.groupby(bin_col).agg(
        simple_avg_forecast=(value_col, 'mean'),
        count=(value_col, 'size')
    ).reset_index()
    
    logger.info(f"Computed simple average for {len(result)} weekly bins.")
    return result

def weighted_average(df: pd.DataFrame, date_col: str = 'date', value_col: str = 'vote_share', weight_col: str = 'historical_rmse', bin_col: str = 'week_bin') -> pd.DataFrame:
    """
    Calculate inverse-RMSE weighted mean, normalizing weights to sum to 1.0 (FR-004).
    
    The weight for each poll is calculated as:
        w_i = (1 / rmse_i) / sum(1 / rmse_j)
    
    If RMSE is 0 or missing, a small epsilon is added to prevent division by zero,
    or the row is handled according to the weights.py logic (default median weight).
    
    Args:
        df: Input DataFrame with columns for date, vote_share, historical_rmse, and week_bin.
        date_col: Name of the date column.
        value_col: Name of the vote share column.
        weight_col: Name of the historical_rmse column.
        bin_col: Name of the weekly bin column.
        
    Returns:
        DataFrame with columns: week_bin, weighted_avg_forecast, total_weight
    """
    if df.empty:
        logger.warning("Input DataFrame is empty for weighted_average.")
        return pd.DataFrame(columns=[bin_col, 'weighted_avg_forecast', 'total_weight'])

    # Ensure weight column is numeric
    df = df.copy()
    df[weight_col] = pd.to_numeric(df[weight_col], errors='coerce')

    # Handle zero or missing RMSE: 
    # If RMSE is 0 or NaN, we cannot compute 1/RMSE. 
    # Based on T012, default median weight logic should ideally be applied earlier,
    # but here we ensure robustness by replacing NaN/Inf with a large RMSE (low weight) 
    # or a small epsilon if we assume 0 means perfect (unlikely in this context, usually means missing).
    # Given T012 assigns a default weight, we assume the input df might already have valid weights.
    # However, to be safe for the inverse calculation:
    df[weight_col] = df[weight_col].replace(0, np.nan) # Treat 0 as missing for inverse calculation
    
    # Calculate inverse RMSE
    df['inv_rmse'] = 1.0 / df[weight_col]
    
    # Fill NaN inv_rmse with 0 (effectively giving 0 weight to missing/invalid RMSE)
    # Alternatively, we could drop these rows, but 0 weight is safer for aggregation.
    df['inv_rmse'] = df['inv_rmse'].fillna(0)

    # Group by bin and calculate weighted mean
    # weighted_mean = sum(w * x) / sum(w)
    def calc_weighted_mean(group):
        w = group['inv_rmse']
        x = group[value_col]
        sum_w = w.sum()
        if sum_w == 0:
            return np.nan # No valid weights
        return np.sum(w * x) / sum_w

    result = df.groupby(bin_col).apply(
        calc_weighted_mean, include_groups=False
    ).reset_index(name='weighted_avg_forecast')
    
    # Also calculate total weight for debugging/verification
    total_weight = df.groupby(bin_col)['inv_rmse'].sum().reset_index(name='total_weight')
    result = result.merge(total_weight, on=bin_col, how='left')

    logger.info(f"Computed weighted average for {len(result)} weekly bins.")
    return result

def main():
    """
    Main entry point to run weighted average calculation on processed data.
    Reads from data/processed/poll_data_cleaned.csv and writes to 
    data/processed/frequentist_forecasts.csv (appending or creating).
    """
    project_root = get_project_root()
    input_path = get_data_processed_path("poll_data_cleaned.csv")
    output_path = get_data_processed_path("frequentist_forecasts.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['date', 'vote_share', 'historical_rmse', 'week_bin']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        sys.exit(1)

    # Run weighted average
    weighted_results = weighted_average(df)
    
    # Run simple average for comparison (if not already present in output)
    simple_results = simple_average(df)
    
    # Merge results
    final_df = weighted_results.merge(simple_results, on='week_bin', how='outer')
    
    # Sort by week_bin
    final_df = final_df.sort_values('week_bin').reset_index(drop=True)
    
    # Save to output
    logger.info(f"Saving forecasts to {output_path}")
    final_df.to_csv(output_path, index=False)
    
    logger.info("Weighted average calculation completed successfully.")
    return final_df

if __name__ == "__main__":
    # Setup logging for standalone execution
    from src.utils.logging import setup_logging
    setup_logging()
    main()
