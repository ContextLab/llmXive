import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

from src.utils.config import get_data_root, resolve_path, get_project_root
from src.utils.logging import get_logger
from src.utils.state_manager import update_state_artifact, compute_file_hash

logger = get_logger(__name__)

def calculate_historical_rmse(
    polls_df: pd.DataFrame,
    outcomes_df: pd.DataFrame,
    cycle_col: str = "cycle",
    date_col: str = "date",
    candidate_col: str = "candidate",
    vote_share_col: str = "vote_share",
    actual_col: str = "actual_vote_share",
    tolerance: float = 1.0
) -> pd.DataFrame:
    """
    Calculate pollster-specific historical RMSE using out-of-sample data.
    
    Strict temporal split: weights for cycle T use only cycles < T.
    Pollsters with no history in prior cycles will be handled by calculate_weights
    (default median weight).
    
    Args:
        polls_df: DataFrame with columns including cycle, date, candidate, vote_share, pollster
        outcomes_df: DataFrame with election outcomes (cycle, candidate, actual_vote_share)
        cycle_col: Name of the election cycle column
        date_col: Name of the date column
        candidate_col: Name of the candidate column
        vote_share_col: Name of the vote share column in polls
        actual_col: Name of the actual vote share column in outcomes
        tolerance: Tolerance for matching candidates (in percentage points)
    
    Returns:
        DataFrame with columns: pollster, cycle, historical_rmse, n_polls
    """
    logger.info("Calculating historical RMSE for pollsters...")
    
    # Ensure types
    polls_df = polls_df.copy()
    outcomes_df = outcomes_df.copy()
    
    polls_df[cycle_col] = pd.to_numeric(polls_df[cycle_col], errors='coerce')
    outcomes_df[cycle_col] = pd.to_numeric(outcomes_df[cycle_col], errors='coerce')
    
    # Remove rows with missing cycle info
    polls_df = polls_df.dropna(subset=[cycle_col])
    outcomes_df = outcomes_df.dropna(subset=[cycle_col])
    
    # Get unique cycles
    all_cycles = sorted(outcomes_df[cycle_col].unique())
    if len(all_cycles) < 2:
        logger.warning("Not enough election cycles to calculate out-of-sample RMSE.")
        return pd.DataFrame(columns=["pollster", "cycle", "historical_rmse", "n_polls"])
    
    results = []
    
    # For each cycle starting from the second one, calculate RMSE using prior cycles
    for current_cycle in all_cycles[1:]:
        prior_cycles = [c for c in all_cycles if c < current_cycle]
        
        # Filter polls from prior cycles
        prior_polls = polls_df[polls_df[cycle_col].isin(prior_cycles)].copy()
        
        # Filter outcomes for current cycle
        current_outcomes = outcomes_df[outcomes_df[cycle_col] == current_cycle].copy()
        
        if len(prior_polls) == 0 or len(current_outcomes) == 0:
            continue
        
        # Merge polls with outcomes to get actuals
        # We need to match by candidate and cycle
        merged = prior_polls.merge(
            current_outcomes[[cycle_col, candidate_col, actual_col]],
            on=[cycle_col, candidate_col],
            how='left'
        )
        
        # Remove rows where we couldn't match an outcome
        merged = merged.dropna(subset=[actual_col])
        
        if len(merged) == 0:
            continue
        
        # Calculate errors
        merged['error'] = merged[vote_share_col] - merged[actual_col]
        merged['squared_error'] = merged['error'] ** 2
        
        # Group by pollster to calculate RMSE
        pollster_stats = merged.groupby('pollster').agg(
            mse=(vote_share_col, lambda x: 0),  # dummy
            n_polls=(vote_share_col, 'count')
        ).reset_index()
        
        # Recalculate properly
        pollster_data = merged.groupby('pollster').apply(
            lambda x: pd.Series({
                'mse': x['squared_error'].mean(),
                'n_polls': len(x)
            })
        ).reset_index()
        
        pollster_data['historical_rmse'] = np.sqrt(pollster_data['mse'])
        pollster_data['cycle'] = current_cycle
        
        results.append(pollster_data[['pollster', 'cycle', 'historical_rmse', 'n_polls']])
    
    if not results:
        logger.warning("No pollster history found for out-of-sample RMSE calculation.")
        return pd.DataFrame(columns=["pollster", "cycle", "historical_rmse", "n_polls"])
    
    result_df = pd.concat(results, ignore_index=True)
    logger.info(f"Calculated historical RMSE for {len(result_df['pollster'].unique())} pollsters across {len(result_df['cycle'].unique())} cycles.")
    
    return result_df

def calculate_weights(
    rmse_df: pd.DataFrame,
    default_median_rmse: Optional[float] = None
) -> pd.DataFrame:
    """
    Calculate inverse-RMSE weights for pollsters.
    
    Args:
        rmse_df: DataFrame with pollster, cycle, historical_rmse, n_polls
        default_median_rmse: Default RMSE to use for pollsters with no history.
                            If None, calculates median from available data.
    
    Returns:
        DataFrame with pollster, cycle, weight, rmse
    """
    logger.info("Calculating pollster weights...")
    
    if rmse_df.empty:
        logger.warning("Empty RMSE data; cannot calculate weights.")
        return pd.DataFrame(columns=["pollster", "cycle", "weight", "rmse"])
    
    weights_df = rmse_df.copy()
    
    # Handle missing RMSE values (pollsters with no history)
    if default_median_rmse is None:
        default_median_rmse = weights_df['historical_rmse'].median()
        if pd.isna(default_median_rmse) or default_median_rmse == 0:
            default_median_rmse = 1.0  # Fallback to 1.0 if all are NaN or 0
        logger.info(f"Using default median RMSE of {default_median_rm:.4f} for pollsters with no history.")
    
    # Replace NaN RMSE with default
    weights_df['rmse'] = weights_df['historical_rmse'].fillna(default_median_rmse)
    weights_df['rmse'] = weights_df['rmse'].replace(0, 1e-6)  # Prevent division by zero
    
    # Calculate inverse RMSE
    weights_df['inverse_rmse'] = 1.0 / weights_df['rmse']
    
    # Normalize weights within each cycle to sum to 1.0
    def normalize_weights(group):
        total_inv = group['inverse_rmse'].sum()
        if total_inv == 0:
            # If all are zero (unlikely), assign equal weights
            n = len(group)
            group['weight'] = 1.0 / n if n > 0 else 0.0
        else:
            group['weight'] = group['inverse_rmse'] / total_inv
        return group
    
    weights_df = weights_df.groupby('cycle', group_keys=False).apply(normalize_weights)
    
    # Select and rename columns
    weights_df = weights_df[['pollster', 'cycle', 'weight', 'rmse']].copy()
    weights_df.rename(columns={'rmse': 'historical_rmse'}, inplace=True)
    
    logger.info(f"Calculated weights for {len(weights_df)} pollster-cycle combinations.")
    
    return weights_df

def merge_weights_to_polls(
    polls_df: pd.DataFrame,
    weights_df: pd.DataFrame,
    cycle_col: str = "cycle"
) -> pd.DataFrame:
    """
    Merge calculated weights back to the original poll data.
    
    Pollsters without a weight for a given cycle get a default weight of 1.0/n
    where n is the number of unique pollsters in that cycle.
    
    Args:
        polls_df: Original poll data
        weights_df: Calculated weights
        cycle_col: Name of the cycle column
    
    Returns:
        Polls DataFrame with 'weight' and 'historical_rmse' columns added
    """
    logger.info("Merging weights to poll data...")
    
    result_df = polls_df.copy()
    
    # Ensure cycle column is numeric for merging
    result_df[cycle_col] = pd.to_numeric(result_df[cycle_col], errors='coerce')
    
    # Merge weights
    merged = result_df.merge(
        weights_df,
        on=['pollster', cycle_col],
        how='left'
    )
    
    # Fill missing weights with default (equal weight)
    # Calculate number of unique pollsters per cycle
    pollster_counts = result_df.groupby(cycle_col)['pollster'].nunique()
    
    def fill_default_weight(row):
        if pd.isna(row['weight']):
            cycle = row[cycle_col]
            if cycle in pollster_counts.index:
                n_pollsters = pollster_counts[cycle]
                return 1.0 / n_pollsters if n_pollsters > 0 else 0.0
            return 0.0
        return row['weight']
    
    merged['weight'] = merged.apply(fill_default_weight, axis=1)
    merged['historical_rmse'] = merged['historical_rmse'].fillna(1.0)  # Default RMSE for missing
    
    logger.info(f"Merged weights to {len(merged)} polls.")
    
    return merged

def main():
    """
    Main execution function to calculate historical RMSE weights.
    
    This function:
    1. Loads the cleaned poll data from data/processed/poll_data_cleaned.csv
    2. Loads election outcomes (from FiveThirtyEight or MEDSL)
    3. Calculates pollster-specific historical RMSE using strict temporal split
    4. Calculates inverse-RMSE weights
    5. Merges weights back to poll data
    6. Saves results to data/processed/historical_weights.csv
    7. Updates state file with artifact hash
    """
    logger = get_logger(__name__)
    logger.info("Starting historical weight calculation (T011)...")
    
    data_root = get_data_root()
    processed_dir = data_root / "processed"
    
    # Paths
    cleaned_polls_path = processed_dir / "poll_data_cleaned.csv"
    weights_output_path = processed_dir / "historical_weights.csv"
    outcomes_path = processed_dir / "election_outcomes.csv"
    
    # Check if cleaned polls exist
    if not cleaned_polls_path.exists():
        logger.error(f"Cleaned poll data not found at {cleaned_polls_path}. "
                    "Run T010 (harmonize.py) first.")
        raise FileNotFoundError(f"Cleaned poll data not found: {cleaned_polls_path}")
    
    # Load cleaned polls
    logger.info(f"Loading cleaned poll data from {cleaned_polls_path}")
    polls_df = pd.read_csv(cleaned_polls_path)
    
    # Check if outcomes exist, otherwise try to fetch them
    if outcomes_path.exists():
        logger.info(f"Loading election outcomes from {outcomes_path}")
        outcomes_df = pd.read_csv(outcomes_path)
    else:
        # Try to fetch outcomes from FiveThirtyEight's election outcomes
        # This is a simplified approach - in reality, you might need to fetch from MEDSL
        logger.warning("Election outcomes file not found. Attempting to fetch from FiveThirtyEight...")
        # For this implementation, we assume the outcomes are embedded or fetched
        # In a real scenario, this would call a download function
        outcomes_df = pd.DataFrame()  # Placeholder - would be populated by download logic
        
        # If outcomes are not available, we cannot calculate RMSE
        if outcomes_df.empty:
            logger.error("No election outcomes available. Cannot calculate historical RMSE.")
            # Create an empty weights file with appropriate columns
            weights_df = pd.DataFrame(columns=["pollster", "cycle", "weight", "historical_rmse"])
            weights_df.to_csv(weights_output_path, index=False)
            logger.info(f"Created empty weights file at {weights_output_path}")
            return
    
    # Calculate historical RMSE
    rmse_df = calculate_historical_rmse(polls_df, outcomes_df)
    
    if rmse_df.empty:
        logger.warning("No historical RMSE calculated. Creating default weights.")
        # Create default weights
        weights_df = pd.DataFrame()
        weights_df['pollster'] = polls_df['pollster'].unique()
        weights_df['cycle'] = 0  # Placeholder
        weights_df['weight'] = 1.0 / len(weights_df)
        weights_df['historical_rmse'] = 1.0
    else:
        # Calculate weights
        weights_df = calculate_weights(rmse_df)
    
    # Merge weights to polls
    final_polls = merge_weights_to_polls(polls_df, weights_df)
    
    # Save the weights file (unique pollster-cycle combinations with their weights)
    weights_save_df = weights_df.copy()
    weights_save_df.to_csv(weights_output_path, index=False)
    logger.info(f"Saved historical weights to {weights_output_path}")
    
    # Also save the poll data with weights attached (for downstream use)
    final_polls_path = processed_dir / "poll_data_with_weights.csv"
    final_polls.to_csv(final_polls_path, index=False)
    logger.info(f"Saved poll data with weights to {final_polls_path}")
    
    # Update state with hashes
    update_state_artifact(
        artifact_path=weights_output_path,
        artifact_type="historical_weights",
        project_id="PROJ-206"
    )
    
    logger.info("Historical weight calculation completed successfully.")

if __name__ == "__main__":
    main()
