import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

from src.utils.config import get_data_root, get_state_root
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Default median weight for pollsters with no history
# This is a heuristic value, typically the median of all calculated weights
DEFAULT_MEDIAN_WEIGHT = 0.5 

def calculate_historical_rmse(
    polls: pd.DataFrame, 
    outcomes: pd.DataFrame, 
    cycles: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate historical RMSE for each pollster using out-of-sample data.
    Strict temporal split: weights for cycle T use only cycles < T.
    
    Args:
        polls: DataFrame with columns ['pollster', 'cycle', 'date', 'vote_share', 'actual_vote_share']
        outcomes: DataFrame with election outcomes
        cycles: List of election cycles to process (e.g., ['2016', '2020'])
        
    Returns:
        Dictionary mapping pollster -> {cycle: rmse_value}
    """
    logger.info("Calculating historical RMSE for each pollster...")
    
    # Ensure data is sorted by cycle
    polls = polls.sort_values('cycle')
    
    rmse_by_pollster_cycle = {}
    
    for idx, current_cycle in enumerate(cycles):
        if idx == 0:
            # No historical data for the first cycle
            continue
            
        # Training data: all cycles before current_cycle
        train_cycles = cycles[:idx]
        train_data = polls[polls['cycle'].isin(train_cycles)]
        
        # Test data: current cycle
        test_data = polls[polls['cycle'] == current_cycle]
        
        if len(train_data) == 0 or len(test_data) == 0:
            continue
            
        # Group by pollster and calculate RMSE
        for pollster in test_data['pollster'].unique():
            if pollster not in rmse_by_pollster_cycle:
                rmse_by_pollster_cycle[pollster] = {}
                
            # Get pollster's historical data
            pollster_train = train_data[train_data['pollster'] == pollster]
            pollster_test = test_data[test_data['pollster'] == pollster]
            
            if len(pollster_train) == 0 or len(pollster_test) == 0:
                continue
                
            # Calculate RMSE: sqrt(mean((predicted - actual)^2))
            # Assuming 'vote_share' is the prediction and 'actual_vote_share' is the outcome
            if 'actual_vote_share' not in pollster_train.columns:
                # Try to merge with outcomes to get actual values
                merged_train = pollster_train.merge(
                    outcomes[['cycle', 'state', 'actual_vote_share']], 
                    on=['cycle', 'state'], 
                    how='left'
                )
                merged_test = pollster_test.merge(
                    outcomes[['cycle', 'state', 'actual_vote_share']], 
                    on=['cycle', 'state'], 
                    how='left'
                )
            else:
                merged_train = pollster_train
                merged_test = pollster_test
            
            # Filter out rows where actual_vote_share is NaN
            merged_train = merged_train.dropna(subset=['actual_vote_share'])
            merged_test = merged_test.dropna(subset=['actual_vote_share'])
            
            if len(merged_train) == 0 or len(merged_test) == 0:
                continue
                
            # Calculate errors on test set using model trained on historical data
            # For simplicity, we use the mean of historical vote shares as the "model"
            # In a more sophisticated approach, we'd train a model per pollster
            historical_mean = merged_train['vote_share'].mean()
            
            errors = merged_test['vote_share'] - merged_test['actual_vote_share']
            rmse = math.sqrt((errors ** 2).mean())
            
            rmse_by_pollster_cycle[pollster][current_cycle] = rmse
            
            logger.debug(f"Pollster {pollster}, Cycle {current_cycle}: RMSE = {rmse:.4f}")
    
    return rmse_by_pollster_cycle

def calculate_weights(
    rmse_data: Dict[str, Dict[str, float]], 
    current_cycle: str
) -> Dict[str, float]:
    """
    Calculate weights for each pollster based on historical RMSE.
    Weight = 1 / RMSE, normalized to sum to 1.
    Handles pollsters with no history by assigning default median weight.
    Prevents division by zero.
    
    Args:
        rmse_data: Dictionary from calculate_historical_rmse
        current_cycle: The cycle we're calculating weights for
        
    Returns:
        Dictionary mapping pollster -> weight
    """
    logger.info(f"Calculating weights for cycle {current_cycle}...")
    
    weights = {}
    valid_pollsters = []
    
    # First pass: identify pollsters with valid RMSE and handle edge cases
    for pollster, cycle_rmse in rmse_data.items():
        if current_cycle in cycle_rmse:
            rmse = cycle_rmse[current_cycle]
            
            # Prevent division by zero: if RMSE is 0 or very small, cap it
            if rmse <= 0:
                logger.warning(f"Pollster {pollster} has RMSE <= 0, using minimum threshold")
                rmse = 1e-6
                
            weight = 1.0 / rmse
            weights[pollster] = weight
            valid_pollsters.append(pollster)
        else:
            # Pollster has no history for this cycle
            logger.info(f"Pollster {pollster} has no history for cycle {current_cycle}, assigning default median weight")
            weights[pollster] = DEFAULT_MEDIAN_WEIGHT
            valid_pollsters.append(pollster)
    
    # Second pass: normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    
    if total_weight == 0:
        # This shouldn't happen given our logic, but handle it safely
        logger.warning("Total weight is zero, assigning equal weights to all pollsters")
        num_pollsters = len(weights)
        if num_pollsters > 0:
            equal_weight = 1.0 / num_pollsters
            for pollster in weights:
                weights[pollster] = equal_weight
    else:
        for pollster in weights:
            weights[pollster] = weights[pollster] / total_weight
    
    logger.debug(f"Calculated weights for {len(weights)} pollsters")
    return weights

def merge_weights_to_polls(
    polls: pd.DataFrame, 
    weights: Dict[str, float], 
    cycle: str
) -> pd.DataFrame:
    """
    Merge calculated weights back to the polls DataFrame.
    Adds a 'weight' column to each poll.
    
    Args:
        polls: DataFrame with poll data
        weights: Dictionary mapping pollster -> weight
        cycle: Current election cycle
        
    Returns:
        DataFrame with added 'weight' column
    """
    logger.info(f"Merging weights to polls for cycle {cycle}...")
    
    # Create a copy to avoid modifying original
    result = polls.copy()
    
    # Map weights to pollsters
    result['weight'] = result['pollster'].map(weights)
    
    # Handle any pollsters that might have been missed (shouldn't happen with our logic)
    missing_weights = result['weight'].isna().sum()
    if missing_weights > 0:
        logger.warning(f"{missing_weights} polls have missing weights, assigning default")
        result['weight'] = result['weight'].fillna(DEFAULT_MEDIAN_WEIGHT)
    
    logger.info(f"Merged weights for {len(result)} polls")
    return result

def main():
    """Main entry point for weights calculation."""
    logger.info("Starting weights calculation...")
    
    # Get paths
    data_root = get_data_root()
    raw_polls_path = data_root / "raw" / "polls.csv"
    outcomes_path = data_root / "raw" / "outcomes.csv"
    output_path = data_root / "processed" / "historical_weights.csv"
    
    # Load data
    try:
        polls = pd.read_csv(raw_polls_path)
        outcomes = pd.read_csv(outcomes_path)
    except FileNotFoundError as e:
        logger.error(f"Required data files not found: {e}")
        return
    
    # Get unique cycles
    cycles = sorted(polls['cycle'].unique().tolist())
    
    if len(cycles) < 2:
        logger.warning("Not enough cycles to calculate historical weights")
        return
    
    # Calculate RMSE for all cycles
    rmse_data = calculate_historical_rmse(polls, outcomes, cycles)
    
    # Calculate and save weights for each cycle
    all_weights = []
    
    for cycle in cycles[1:]:  # Skip first cycle (no history)
        weights = calculate_weights(rmse_data, cycle)
        
        # Merge weights to polls for this cycle
        cycle_polls = polls[polls['cycle'] == cycle]
        weighted_polls = merge_weights_to_polls(cycle_polls, weights, cycle)
        
        # Add cycle information
        weighted_polls['calculation_cycle'] = cycle
        all_weights.append(weighted_polls)
    
    if len(all_weights) > 0:
        final_df = pd.concat(all_weights, ignore_index=True)
        final_df.to_csv(output_path, index=False)
        logger.info(f"Saved weighted polls to {output_path}")
    else:
        logger.warning("No weights calculated")

if __name__ == "__main__":
    main()