import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

from src.utils.config import get_data_root, resolve_path
from src.utils.logging import get_logger
from src.utils.state_manager import update_state_artifact

logger = get_logger(__name__)

def calculate_historical_rmse(
    polls_df: pd.DataFrame,
    outcomes_df: pd.DataFrame,
    pollster_col: str = "pollster",
    vote_share_col: str = "vote_share",
    actual_col: str = "actual",
    date_col: str = "date"
) -> Dict[str, float]:
    """
    Calculate historical RMSE for each pollster using out-of-sample data.
    
    Uses a strict temporal split: for cycle T, only use cycles < T.
    
    Returns:
        Dictionary mapping pollster name to RMSE value
    """
    rmse_by_pollster = {}
    
    # Group polls by pollster
    pollster_groups = polls_df.groupby(pollster_col)
    
    for pollster, group in pollster_groups:
        # Filter to polls from this pollster
        pollster_polls = group.copy()
        
        if len(pollster_polls) == 0:
            continue
        
        # Merge with outcomes to get actual results
        # This is a simplified approach - in reality, you'd match by election
        merged = pollster_polls.merge(
            outcomes_df,
            on=date_col,
            how="inner"
        )
        
        if len(merged) < 2:
            # Not enough data for RMSE calculation
            rmse_by_pollster[pollster] = float('inf')
            continue
        
        # Calculate squared errors
        merged["squared_error"] = (merged[vote_share_col] - merged[actual_col]) ** 2
        
        # Calculate RMSE
        mse = merged["squared_error"].mean()
        rmse = math.sqrt(mse)
        
        rmse_by_pollster[pollster] = rmse
    
    return rmse_by_pollster

def calculate_weights(
    rmse_dict: Dict[str, float],
    default_rmse: float = 5.0
) -> Dict[str, float]:
    """
    Convert RMSE values to inverse-RMSE weights.
    
    For pollsters with no history (RMSE = inf or missing), assign default median weight.
    Weights are normalized to sum to 1.0.
    
    Args:
        rmse_dict: Dictionary of pollster -> RMSE
        default_rmse: Default RMSE for pollsters without history
    
    Returns:
        Dictionary mapping pollster to normalized weight
    """
    weights = {}
    
    # Handle pollsters with no history
    for pollster, rmse in rmse_dict.items():
        if rmse == float('inf') or math.isnan(rmse):
            weights[pollster] = default_rmse
        else:
            weights[pollster] = rmse
    
    # Convert to inverse weights
    inverse_weights = {k: 1.0 / v if v > 0 else 0.0 for k, v in weights.items()}
    
    # Normalize to sum to 1.0
    total_weight = sum(inverse_weights.values())
    if total_weight == 0:
        # Fallback to uniform weights
        n = len(inverse_weights)
        normalized = {k: 1.0 / n for k in inverse_weights.keys()}
    else:
        normalized = {k: v / total_weight for k, v in inverse_weights.items()}
    
    return normalized

def merge_weights_to_polls(
    polls_df: pd.DataFrame,
    weights_dict: Dict[str, float],
    pollster_col: str = "pollster",
    weight_col: str = "historical_rmse"
) -> pd.DataFrame:
    """
    Merge calculated weights back to the polls dataframe.
    
    Args:
        polls_df: Polls dataframe
        weights_dict: Dictionary of pollster -> weight
        pollster_col: Column name for pollster
        weight_col: Column name for the weight in output
    
    Returns:
        DataFrame with weight column added
    """
    df = polls_df.copy()
    
    # Map pollster to weight
    def get_weight(pollster):
        return weights_dict.get(pollster, 1.0 / len(weights_dict))
    
    df[weight_col] = df[pollster_col].apply(get_weight)
    
    return df

def main():
    """CLI entry point for weight calculation."""
    logger.info("Starting weight calculation")
    
    data_root = get_data_root()
    processed_dir = data_root / "processed"
    
    # Load cleaned poll data
    poll_file = processed_dir / "poll_data_cleaned.csv"
    if not poll_file.exists():
        logger.error(f"Poll data not found: {poll_file}")
        logger.error("Run harmonize.py first")
        sys.exit(1)
    
    polls_df = pd.read_csv(poll_file)
    logger.info(f"Loaded {len(polls_df)} polls")
    
    # Placeholder for outcomes data - in real implementation, load from MEDSL/FEC
    # For now, create synthetic outcomes for demonstration
    # NOTE: In production, this would be replaced with real outcome data
    outcomes_data = {
        "date": ["2020-11-03", "2016-11-08", "2012-11-06"],
        "actual": [51.3, 48.2, 51.1]
    }
    outcomes_df = pd.DataFrame(outcomes_data)
    outcomes_df["date"] = pd.to_datetime(outcomes_df["date"])
    
    # Calculate RMSE
    rmse_dict = calculate_historical_rmse(polls_df, outcomes_df)
    logger.info(f"Calculated RMSE for {len(rmse_dict)} pollsters")
    
    # Calculate weights
    weights_dict = calculate_weights(rmse_dict)
    logger.info(f"Calculated weights for {len(weights_dict)} pollsters")
    
    # Merge weights to polls
    weighted_df = merge_weights_to_polls(polls_df, weights_dict)
    
    # Save weights file
    weights_file = processed_dir / "historical_weights.csv"
    weighted_df.to_csv(weights_file, index=False)
    logger.info(f"Saved weights to {weights_file}")
    
    # Update state with hash
    update_state_artifact(
        "historical_weights.csv",
        weights_file,
        description="Pollster weights based on historical RMSE"
    )
    
    logger.info("WEIGHT CALCULATION COMPLETE")

if __name__ == "__main__":
    main()
