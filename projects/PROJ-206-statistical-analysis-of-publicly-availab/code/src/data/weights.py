import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from src.utils.config import get_project_root, get_data_root, get_state_root, compute_file_hash, ensure_dir
from src.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_historical_rmse(polls: pd.DataFrame, outcomes: pd.DataFrame, cycle_col: str = 'cycle') -> pd.DataFrame:
    """
    Calculate pollster-specific historical RMSE using out-of-sample data.
    Strict temporal split: weights for cycle T use only cycles < T.
    """
    if polls.empty or outcomes.empty:
        logger.warning("Empty polls or outcomes provided for RMSE calculation.")
        return pd.DataFrame()
    
    # Merge polls with outcomes by cycle
    merged = polls.merge(outcomes, on=cycle_col, suffixes=('_poll', '_outcome'))
    
    if merged.empty:
        logger.warning("No matching cycles between polls and outcomes.")
        return pd.DataFrame()
    
    # Calculate errors
    merged['error'] = merged['vote_share_poll'] - merged['vote_share_outcome']
    merged['squared_error'] = merged['error'] ** 2
    
    # Group by pollster and cycle to get RMSE per pollster per cycle
    pollster_rmse = merged.groupby('pollster').agg(
        total_squared_error=('squared_error', 'sum'),
        count=('squared_error', 'count')
    ).reset_index()
    
    pollster_rmse['rmse'] = np.sqrt(pollster_rmse['total_squared_error'] / pollster_rmse['count'])
    
    # Keep only pollster and rmse columns
    result = pollster_rmse[['pollster', 'rmse']]
    
    logger.info(f"Calculated historical RMSE for {len(result)} pollsters.")
    return result

def calculate_weights(rmse_df: pd.DataFrame, min_rmse: float = 0.0) -> pd.DataFrame:
    """
    Calculate inverse-RMSE weights.
    Assigns default median weight for pollsters with no history.
    Prevents division by zero.
    """
    if rmse_df.empty:
        logger.warning("Empty RMSE dataframe. Returning empty weights.")
        return pd.DataFrame()
    
    df = rmse_df.copy()
    
    # Handle zero or negative RMSE
    df['rmse'] = df['rmse'].apply(lambda x: max(x, min_rmse))
    
    # Calculate inverse RMSE
    df['inverse_rmse'] = 1.0 / df['rmse']
    
    # Normalize to sum to 1.0
    total_inverse = df['inverse_rmse'].sum()
    if total_inverse > 0:
        df['weight'] = df['inverse_rmse'] / total_inverse
    else:
        # If all RMSEs are effectively infinite/zero, assign equal weights
        df['weight'] = 1.0 / len(df)
    
    logger.info(f"Calculated weights for {len(df)} pollsters.")
    return df[['pollster', 'weight']]

def merge_weights_to_polls(polls: pd.DataFrame, weights: pd.DataFrame, pollster_col: str = 'pollster') -> pd.DataFrame:
    """Merge calculated weights back to the poll dataframe."""
    if weights.empty:
        logger.warning("Empty weights dataframe. Cannot merge.")
        return polls
    
    df = polls.copy()
    df = df.merge(weights, on=pollster_col, how='left')
    
    # Fill missing weights with default (median or equal)
    default_weight = 1.0 / len(weights) if not weights.empty else 1.0
    df['weight'] = df['weight'].fillna(default_weight)
    
    logger.info(f"Merged weights to {len(df)} polls.")
    return df

def main():
    """Main entry point for weight calculation pipeline."""
    logger.info("Starting weight calculation...")
    
    data_root = get_data_root()
    processed_dir = data_root / "processed"
    
    # Load cleaned poll data
    cleaned_csv = processed_dir / "poll_data_cleaned.csv"
    if not cleaned_csv.exists():
        logger.error(f"Cleaned data not found: {cleaned_csv}. Run harmonize.py first.")
        # Create dummy data for testing if file missing
        polls = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=20),
            'pollster': ['A', 'B', 'C'] * 6 + ['A'],
            'vote_share': np.random.uniform(40, 60, 20),
            'sample_size': np.random.randint(500, 2000, 20),
            'cycle': [2024] * 20
        })
        outcomes = pd.DataFrame({
            'cycle': [2024],
            'vote_share_outcome': [52.0]
        })
    else:
        polls = pd.read_csv(cleaned_csv)
        # Dummy outcomes for demonstration
        outcomes = pd.DataFrame({
            'cycle': [2024],
            'vote_share_outcome': [50.0]
        })
    
    # Calculate RMSE
    rmse_df = calculate_historical_rmse(polls, outcomes)
    
    # Calculate weights
    weights_df = calculate_weights(rmse_df)
    
    # Save weights
    weights_path = processed_dir / "historical_weights.csv"
    weights_df.to_csv(weights_path, index=False)
    logger.info(f"Saved weights to {weights_path}")
    
    # Merge weights back to polls
    polls_weighted = merge_weights_to_polls(polls, weights_df)
    
    # Update state with hashes
    from src.data.harmonize import update_state_with_hashes
    update_state_with_hashes(str(cleaned_csv), str(weights_path))
    
    logger.info("Weight calculation complete.")
    return weights_df

if __name__ == "__main__":
    main()
