"""
weights.py - Calculate and apply historical pollster weights.

This module implements the calculation of historical RMSE for pollsters
based on out-of-sample performance and assigns weights for aggregation.
It specifically handles edge cases for pollsters with no history and
prevents division by zero during weight normalization.
"""

import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

from src.utils.config import get_data_root, resolve_path
from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_historical_rmse(
    polls_df: pd.DataFrame,
    outcomes_df: pd.DataFrame,
    election_cycle_col: str = 'cycle',
    date_col: str = 'date',
    vote_share_col: str = 'vote_share',
    actual_col: str = 'actual_vote_share',
    pollster_col: str = 'pollster'
) -> pd.DataFrame:
    """
    Calculate historical RMSE for each pollster using out-of-sample data.

    For a given election cycle T, we calculate RMSE using data from cycles < T.
    This ensures we are not leaking information from the current election into
    the weight calculation for that same election.

    Args:
        polls_df: DataFrame containing poll data with columns for date,
                  vote_share, pollster, and cycle.
        outcomes_df: DataFrame containing actual election outcomes with
                     columns for actual_vote_share and cycle.
        election_cycle_col: Name of the column representing the election cycle.
        date_col: Name of the column representing the poll date.
        vote_share_col: Name of the column representing the poll vote share.
        actual_col: Name of the column representing the actual vote share.
        pollster_col: Name of the column representing the pollster.

    Returns:
        A DataFrame with columns: pollster, cycle, historical_rmse
    """
    logger.info("Calculating historical RMSE for pollsters...")

    # Ensure we have the necessary columns
    required_cols = [election_cycle_col, date_col, vote_share_col, pollster_col]
    if not all(col in polls_df.columns for col in required_cols):
        raise ValueError(f"polls_df missing required columns: {required_cols}")

    if not all(col in outcomes_df.columns for col in [election_cycle_col, actual_col]):
        raise ValueError(f"outcomes_df missing required columns: {[election_cycle_col, actual_col]}")

    # Merge polls with outcomes to get actual results
    merged = polls_df.merge(
        outcomes_df[[election_cycle_col, actual_col]],
        on=election_cycle_col,
        how='left'
    )

    # Filter to polls that have an actual outcome (i.e., past elections)
    merged = merged[merged[actual_col].notna()].copy()

    if merged.empty:
        logger.warning("No polls with corresponding actual outcomes found. Cannot calculate RMSE.")
        return pd.DataFrame(columns=['pollster', 'cycle', 'historical_rmse'])

    # Calculate error for each poll
    merged['error'] = merged[vote_share_col] - merged[actual_col]
    merged['squared_error'] = merged['error'] ** 2

    # For each cycle T, we want to calculate RMSE using data from cycles < T
    # First, group by pollster and cycle to get RMSE for that specific cycle
    cycle_rmse = merged.groupby([pollster_col, election_cycle_col]).agg({
        'squared_error': 'mean',
        'error': 'count'
    }).reset_index()
    cycle_rmse['rmse'] = np.sqrt(cycle_rmse['squared_error'])
    cycle_rmse = cycle_rmse.rename(columns={'error': 'poll_count'})

    # Now, for each cycle T, calculate the cumulative RMSE from all previous cycles
    all_cycles = sorted(cycle_rmse[election_cycle_col].unique())
    results = []

    for pollster in cycle_rmse[pollster_col].unique():
        pollster_data = cycle_rmse[cycle_rmse[pollster_col] == pollster].sort_values(election_cycle_col)
        
        cumulative_squared_error = 0.0
        cumulative_count = 0
        
        for current_cycle in all_cycles:
            # Get data for cycles strictly less than current_cycle
            prev_data = pollster_data[pollster_data[election_cycle_col] < current_cycle]
            
            if not prev_data.empty:
                # Calculate RMSE from previous cycles only
                total_sq_error = prev_data['squared_error'].sum()
                total_count = prev_data['poll_count'].sum()
                
                if total_count > 0:
                    rmse = np.sqrt(total_sq_error / total_count)
                else:
                    rmse = np.nan
            else:
                # No history for this pollster in previous cycles
                rmse = np.nan
            
            results.append({
                pollster_col: pollster,
                election_cycle_col: current_cycle,
                'historical_rmse': rmse
            })

    rmse_df = pd.DataFrame(results)
    logger.info(f"Calculated historical RMSE for {rmse_df[pollster_col].nunique()} pollsters.")
    
    return rmse_df


def calculate_weights(
    rmse_df: pd.DataFrame,
    cycle_col: str = 'cycle',
    rmse_col: str = 'historical_rmse',
    pollster_col: str = 'pollster'
) -> pd.DataFrame:
    """
    Calculate weights for pollsters based on historical RMSE.

    Weights are calculated as the inverse of RMSE, normalized to sum to 1.0.
    Pollsters with no history (RMSE is NaN) are assigned a default median weight.

    Args:
        rmse_df: DataFrame containing pollster, cycle, and historical_rmse.
        cycle_col: Name of the column representing the election cycle.
        rmse_col: Name of the column representing the historical RMSE.
        pollster_col: Name of the column representing the pollster.

    Returns:
        A DataFrame with columns: pollster, cycle, weight
    """
    logger.info("Calculating weights from historical RMSE...")

    if rmse_df.empty:
        logger.warning("RMSE DataFrame is empty. Cannot calculate weights.")
        return pd.DataFrame(columns=['pollster', 'cycle', 'weight'])

    weights_df = rmse_df.copy()

    # Calculate median RMSE for pollsters with valid RMSE
    valid_rmse = weights_df[rmse_col].dropna()
    if len(valid_rmse) > 0:
        median_rmse = valid_rmse.median()
    else:
        median_rmse = 1.0  # Default fallback if no valid RMSE exists
    
    logger.info(f"Median historical RMSE: {median_rmse:.4f}")

    # Assign median RMSE to pollsters with no history (NaN)
    weights_df[rmse_col] = weights_df[rmse_col].fillna(median_rmse)

    # Calculate inverse RMSE weights
    # To prevent division by zero, we ensure RMSE is never 0
    weights_df['inverse_rmse'] = 1.0 / np.maximum(weights_df[rmse_col], 1e-9)

    # Normalize weights to sum to 1.0 within each cycle
    def normalize_weights(group):
        total_weight = group['inverse_rmse'].sum()
        if total_weight > 0:
            group['weight'] = group['inverse_rmse'] / total_weight
        else:
            # If all weights are effectively zero, distribute equally
            group['weight'] = 1.0 / len(group)
        return group

    weights_df = weights_df.groupby(cycle_col, group_keys=False).apply(normalize_weights)

    # Keep only relevant columns
    weights_df = weights_df[[pollster_col, cycle_col, 'weight']].reset_index(drop=True)

    logger.info(f"Calculated weights for {weights_df[pollster_col].nunique()} pollsters across {weights_df[cycle_col].nunique()} cycles.")
    
    return weights_df


def merge_weights_to_polls(
    polls_df: pd.DataFrame,
    weights_df: pd.DataFrame,
    cycle_col: str = 'cycle',
    pollster_col: str = 'pollster',
    rmse_col: str = 'historical_rmse'
) -> pd.DataFrame:
    """
    Merge calculated weights back to the poll data.

    Args:
        polls_df: DataFrame containing poll data.
        weights_df: DataFrame containing calculated weights.
        cycle_col: Name of the column representing the election cycle.
        pollster_col: Name of the column representing the pollster.
        rmse_col: Name of the column for historical RMSE in the output.

    Returns:
        A DataFrame with poll data merged with weights and historical RMSE.
    """
    logger.info("Merging weights to poll data...")

    if weights_df.empty:
        logger.warning("Weights DataFrame is empty. Returning polls without weights.")
        polls_df['weight'] = 1.0
        polls_df[rmse_col] = np.nan
        return polls_df

    # Merge weights onto polls
    merged = polls_df.merge(
        weights_df[[pollster_col, cycle_col, 'weight']],
        on=[pollster_col, cycle_col],
        how='left'
    )

    # Fill missing weights with equal weight (1/n_pollsters for that cycle)
    # First, calculate the number of pollsters per cycle with valid weights
    cycle_pollster_counts = merged.groupby(cycle_col)[pollster_col].nunique()
    
    def fill_missing_weights(group):
        missing_mask = group['weight'].isna()
        if missing_mask.any():
            # Count how many pollsters in this cycle have valid weights
            valid_count = group['weight'].notna().sum()
            if valid_count > 0:
                # Sum of existing weights
                existing_weight_sum = group['weight'].sum()
                remaining_weight = 1.0 - existing_weight_sum
                num_missing = missing_mask.sum()
                if num_missing > 0 and remaining_weight > 0:
                    group.loc[missing_mask, 'weight'] = remaining_weight / num_missing
                else:
                    # Fallback: distribute equally among all in cycle
                    group['weight'] = 1.0 / len(group)
            else:
                # No valid weights in this cycle, distribute equally
                group['weight'] = 1.0 / len(group)
        return group

    merged = merged.groupby(cycle_col, group_keys=False).apply(fill_missing_weights)

    # Add historical RMSE column (we can merge it back if needed, or calculate on the fly)
    # For simplicity, we'll leave it as NaN for now if not available
    if rmse_col not in merged.columns:
        merged[rmse_col] = np.nan

    logger.info(f"Merged weights for {len(merged)} polls.")
    
    return merged


def main():
    """
    Main function to run the weight calculation pipeline.

    This function:
    1. Loads raw poll data and election outcomes.
    2. Calculates historical RMSE for each pollster.
    3. Calculates weights based on inverse RMSE.
    4. Merges weights back to the poll data.
    5. Saves the weighted poll data and weights to CSV files.
    """
    logger.info("Starting weight calculation pipeline...")

    data_root = get_data_root()
    processed_dir = data_root / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load processed poll data (from harmonize.py)
    poll_data_path = processed_dir / 'poll_data_cleaned.csv'
    if not poll_data_path.exists():
        logger.error(f"Poll data not found at {poll_data_path}. Please run harmonize.py first.")
        return

    polls_df = pd.read_csv(poll_data_path)
    logger.info(f"Loaded {len(polls_df)} polls from {poll_data_path}")

    # Load election outcomes (should be in data/raw or data/processed)
    outcomes_path = processed_dir / 'election_outcomes.csv'
    if not outcomes_path.exists():
        # Try raw directory
        outcomes_path = data_root / 'raw' / 'election_outcomes.csv'
    
    if not outcomes_path.exists():
        logger.error(f"Election outcomes not found at {outcomes_path}. Please download election outcomes first.")
        return

    outcomes_df = pd.read_csv(outcomes_path)
    logger.info(f"Loaded {len(outcomes_df)} election outcomes from {outcomes_path}")

    # Calculate historical RMSE
    rmse_df = calculate_historical_rmse(polls_df, outcomes_df)
    rmse_path = processed_dir / 'historical_rmse.csv'
    rmse_df.to_csv(rmse_path, index=False)
    logger.info(f"Saved historical RMSE to {rmse_path}")

    # Calculate weights
    weights_df = calculate_weights(rmse_df)
    weights_path = processed_dir / 'historical_weights.csv'
    weights_df.to_csv(weights_path, index=False)
    logger.info(f"Saved historical weights to {weights_path}")

    # Merge weights to polls
    weighted_polls_df = merge_weights_to_polls(polls_df, weights_df)
    weighted_polls_path = processed_dir / 'poll_data_weighted.csv'
    weighted_polls_df.to_csv(weighted_polls_path, index=False)
    logger.info(f"Saved weighted poll data to {weighted_polls_path}")

    logger.info("Weight calculation pipeline completed successfully.")


if __name__ == '__main__':
    main()
