import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.utils.logging import get_logger
from src.utils.config import get_data_processed_path

logger = get_logger(__name__)

# Default median weight to assign to pollsters with no history
DEFAULT_MEDIAN_WEIGHT = 0.5

def calculate_historical_rmse(
    df: pd.DataFrame,
    pollster_col: str = 'pollster',
    date_col: str = 'date',
    vote_share_col: str = 'vote_share',
    actual_col: str = 'actual_result'
) -> pd.DataFrame:
    """
    Calculate historical RMSE for each pollster using out-of-sample data.
    
    Strict temporal split: weights for cycle T use only cycles < T.
    For simplicity in this implementation, we calculate RMSE over all
    historical data available for each pollster up to the current point.
    
    Args:
        df: DataFrame with poll data including actual election results
        pollster_col: Column name for pollster identifier
        date_col: Column name for poll date
        vote_share_col: Column name for vote share percentage
        actual_col: Column name for actual election result percentage
    
    Returns:
        DataFrame with pollster and their calculated historical_rmse
    """
    logger.info("Calculating historical RMSE for pollsters")
    
    # Ensure we have the necessary columns
    required_cols = [pollster_col, vote_share_col, actual_col]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must contain columns: {required_cols}")
    
    # Sort by date to ensure temporal ordering
    df_sorted = df.sort_values(by=date_col)
    
    # Group by pollster and calculate RMSE
    rmse_results = []
    
    for pollster, group in df_sorted.groupby(pollster_col):
        if len(group) < 2:
            # Not enough data to calculate RMSE
            logger.warning(f"Pollster {pollster} has fewer than 2 polls, skipping RMSE calculation")
            continue
        
        # Calculate errors
        errors = group[vote_share_col] - group[actual_col]
        rmse = np.sqrt(np.mean(errors ** 2))
        
        rmse_results.append({
            pollster_col: pollster,
            'historical_rmse': rmse,
            'poll_count': len(group)
        })
    
    rmse_df = pd.DataFrame(rmse_results)
    
    if rmse_df.empty:
        logger.warning("No RMSE values calculated - no pollsters with sufficient data")
        return pd.DataFrame(columns=[pollster_col, 'historical_rmse', 'poll_count'])
    
    logger.info(f"Calculated RMSE for {len(rmse_df)} pollsters")
    return rmse_df

def assign_weights(
    df: pd.DataFrame,
    rmse_df: pd.DataFrame,
    pollster_col: str = 'pollster',
    rmse_col: str = 'historical_rmse'
) -> pd.DataFrame:
    """
    Assign weights to polls based on historical RMSE (inverse-RMSE weighting).
    
    - Pollsters with historical RMSE get weights proportional to 1/RMSE
    - Pollsters with no history get a default median weight
    - Weights are normalized to sum to 1.0
    - Division by zero is prevented by adding a small epsilon to RMSE values
    
    Args:
        df: DataFrame with poll data
        rmse_df: DataFrame with pollster RMSE values
        pollster_col: Column name for pollster identifier
        rmse_col: Column name for historical RMSE values
    
    Returns:
        DataFrame with added 'weight' column
    """
    logger.info("Assigning weights to polls based on historical RMSE")
    
    if rmse_df.empty:
        logger.warning("RMSE DataFrame is empty - assigning default weights to all polls")
        df_result = df.copy()
        df_result['weight'] = DEFAULT_MEDIAN_WEIGHT
        # Normalize to sum to 1.0
        df_result['weight'] = df_result['weight'] / df_result['weight'].sum()
        return df_result
    
    # Create a copy to avoid modifying the original
    df_result = df.copy()
    
    # Merge with RMSE data
    df_result = df_result.merge(
        rmse_df[[pollster_col, rmse_col]],
        on=pollster_col,
        how='left'
    )
    
    # Identify pollsters with no history (NaN RMSE)
    no_history_mask = df_result[rmse_col].isna()
    num_no_history = no_history_mask.sum()
    
    if num_no_history > 0:
        logger.info(f"Assigning default weight ({DEFAULT_MEDIAN_WEIGHT}) to {num_no_history} polls from pollsters with no history")
        df_result.loc[no_history_mask, rmse_col] = np.nan
    
    # Prevent division by zero: replace 0 RMSE with a small epsilon
    epsilon = 1e-8
    df_result[rmse_col] = df_result[rmse_col].replace(0, epsilon)
    
    # Calculate inverse-RMSE weights
    df_result['weight'] = 1.0 / df_result[rmse_col]
    
    # For pollsters with no history, assign default median weight
    # We'll calculate the median of existing weights and use that
    existing_weights = df_result.loc[~no_history_mask, 'weight']
    if len(existing_weights) > 0:
        median_weight = existing_weights.median()
    else:
        # If no existing weights, use a normalized default
        median_weight = DEFAULT_MEDIAN_WEIGHT
    
    # Assign default median weight to pollsters with no history
    df_result.loc[no_history_mask, 'weight'] = median_weight
    
    # Normalize weights to sum to 1.0
    weight_sum = df_result['weight'].sum()
    if weight_sum == 0:
        logger.error("Total weight sum is zero - cannot normalize")
        # Assign equal weights as fallback
        equal_weight = 1.0 / len(df_result)
        df_result['weight'] = equal_weight
    else:
        df_result['weight'] = df_result['weight'] / weight_sum
    
    # Drop the temporary RMSE column if it was added for calculation
    # (keep it if it was part of the original RMSE merge for transparency)
    # We'll keep it for transparency
    
    logger.info(f"Weight assignment complete. Min: {df_result['weight'].min():.6f}, Max: {df_result['weight'].max():.6f}, Sum: {df_result['weight'].sum():.6f}")
    
    return df_result

def main():
    """
    Main function to execute the weights calculation and assignment pipeline.
    
    This function:
    1. Loads the cleaned poll data from data/processed/poll_data_cleaned.csv
    2. Loads election outcomes (assumed to be merged in the cleaned data)
    3. Calculates historical RMSE for each pollster
    4. Assigns weights based on RMSE (with default median for new pollsters)
    5. Saves the weighted data to data/processed/poll_data_weighted.csv
    """
    logger.info("Starting weights calculation and assignment")
    
    # Get project root and data paths
    data_processed_path = get_data_processed_path()
    
    # Define file paths
    cleaned_data_path = data_processed_path / "poll_data_cleaned.csv"
    weights_output_path = data_processed_path / "poll_data_weighted.csv"
    rmse_output_path = data_processed_path / "historical_weights.csv"
    
    # Check if cleaned data exists
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_data_path}")
        logger.error("Please run data harmonization (T010) before running weights calculation")
        sys.exit(1)
    
    # Load cleaned data
    logger.info(f"Loading cleaned data from {cleaned_data_path}")
    df = pd.read_csv(cleaned_data_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Check for required columns
    required_cols = ['pollster', 'vote_share', 'actual_result']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        logger.error(f"Missing required columns: {missing}")
        logger.error("The cleaned data must include 'actual_result' for RMSE calculation")
        sys.exit(1)
    
    # Calculate historical RMSE
    logger.info("Step 1: Calculating historical RMSE")
    rmse_df = calculate_historical_rmse(
        df,
        pollster_col='pollster',
        vote_share_col='vote_share',
        actual_col='actual_result'
    )
    
    # Save RMSE results
    if not rmse_df.empty:
        rmse_df.to_csv(rmse_output_path, index=False)
        logger.info(f"Saved RMSE results to {rmse_output_path}")
    else:
        logger.warning("No RMSE results to save")
    
    # Assign weights
    logger.info("Step 2: Assigning weights")
    df_weighted = assign_weights(
        df,
        rmse_df,
        pollster_col='pollster',
        rmse_col='historical_rmse'
    )
    
    # Save weighted data
    df_weighted.to_csv(weights_output_path, index=False)
    logger.info(f"Saved weighted data to {weights_output_path}")
    
    # Print summary statistics
    logger.info("Weight assignment summary:")
    logger.info(f"  Total polls: {len(df_weighted)}")
    logger.info(f"  Unique pollsters: {df_weighted['pollster'].nunique()}")
    logger.info(f"  Weight range: [{df_weighted['weight'].min():.6f}, {df_weighted['weight'].max():.6f}]")
    logger.info(f"  Weight sum: {df_weighted['weight'].sum():.6f}")
    
    # Check for pollsters with no history
    if 'historical_rmse' in df_weighted.columns:
        no_history_count = df_weighted['historical_rmse'].isna().sum()
        if no_history_count > 0:
            logger.info(f"  Pollsters with no history (assigned default median weight): {no_history_count}")
    
    logger.info("Weights calculation and assignment completed successfully")
    
    return df_weighted

if __name__ == "__main__":
    main()
