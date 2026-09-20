import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

def filter_trials(trials: pd.DataFrame, min_rt: float = 300.0, max_rt: float = 10000.0) -> pd.DataFrame:
    """
    Filter trials based on reaction time bounds and error handling.
    
    Parameters:
    - trials: DataFrame with columns including 'reaction_time' and 'is_correct'
    - min_rt: Minimum valid reaction time in ms (default 300ms)
    - max_rt: Maximum valid reaction time in ms (default 10000ms)
    
    Returns:
    - Filtered DataFrame
    """
    logger.info(f"Filtering trials with bounds: {min_rt}ms <= RT <= {max_rt}ms")
    
    # Filter by reaction time bounds
    valid_trials = trials[
        (trials['reaction_time'] >= min_rt) & 
        (trials['reaction_time'] <= max_rt)
    ]
    
    # Log exclusion statistics
    excluded_count = len(trials) - len(valid_trials)
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} trials due to RT bounds")
    
    return valid_trials

def calculate_d_score(trials: pd.DataFrame) -> float:
    """
    Calculate the Greenwald D2 score for a set of trials.
    
    The D2 algorithm (Greenwald et al., 2003) computes the implicit association
    test score as the difference in mean reaction times between two blocks,
    divided by the standard deviation of all trials in both blocks.
    
    Parameters:
    - trials: DataFrame containing trials for both blocks (e.g., 'compatible' and 'incompatible')
      Expected columns: 'reaction_time', 'is_correct', 'block_type' (or similar indicator)
    
    Returns:
    - D-score (float)
    """
    if len(trials) < 2:
        logger.warning("Insufficient trials for D-score calculation")
        return np.nan

    # Ensure we have the necessary columns
    if 'block_type' not in trials.columns:
        # If no block type, assume all trials are one block (not typical for IAT)
        # This is a fallback; typically IAT requires two blocks
        logger.warning("No block_type column found; assuming single block (invalid for IAT)")
        return np.nan

    # Separate blocks
    # Assuming block_type values are 'compatible' and 'incompatible'
    # Adjust if the data uses different naming
    compatible = trials[trials['block_type'] == 'compatible']
    incompatible = trials[trials['block_type'] == 'incompatible']

    if len(compatible) == 0 or len(incompatible) == 0:
        logger.warning("Missing trials in one or both blocks")
        return np.nan

    # Mean reaction times
    mean_compatible = compatible['reaction_time'].mean()
    mean_incompatible = incompatible['reaction_time'].mean()

    # Standard deviation of all trials (pooled)
    all_rt = pd.concat([compatible['reaction_time'], incompatible['reaction_time']])
    std_all = all_rt.std()

    # D2 formula: (Mean_incompatible - Mean_compatible) / SD_all
    if std_all == 0:
        logger.warning("Standard deviation is zero; cannot compute D-score")
        return np.nan

    d_score = (mean_incompatible - mean_compatible) / std_all
    
    logger.info(f"Calculated D-score: {d_score:.4f}")
    return d_score

def load_raw_logs_to_dict(raw_logs: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Load raw response logs into a dictionary keyed by participant ID.
    
    Parameters:
    - raw_logs: List of DataFrames, each representing raw response logs
    
    Returns:
    - Dictionary: {participant_id: DataFrame}
    """
    result = {}
    for df in raw_logs:
        if 'participant_id' not in df.columns:
            raise ValueError("Input DataFrames must contain 'participant_id' column")
        
        for pid, group in df.groupby('participant_id'):
            if pid not in result:
                result[pid] = pd.DataFrame()
            result[pid] = pd.concat([result[pid], group], ignore_index=True)
    
    return result

def aggregate_d_scores(
    filtered_trials: pd.DataFrame,
    min_valid_trials: int = 10
) -> pd.DataFrame:
    """
    Aggregate D-scores for each participant-session combination.
    
    Parameters:
    - filtered_trials: DataFrame with filtered trials (after RT filtering)
    - min_valid_trials: Minimum number of valid trials required to compute D-score
    
    Returns:
    - DataFrame with columns: participant_id, session_id, d_score, n_trials_valid, status
    """
    logger.info(f"Aggregating D-scores with min_valid_trials={min_valid_trials}")
    
    if 'participant_id' not in filtered_trials.columns or 'session_id' not in filtered_trials.columns:
        raise ValueError("Input DataFrame must contain 'participant_id' and 'session_id' columns")
    
    results = []
    
    # Group by participant and session
    for (pid, sid), group in filtered_trials.groupby(['participant_id', 'session_id']):
        n_trials = len(group)
        
        if n_trials < min_valid_trials:
            d_score = np.nan
            status = 'insufficient_trials'
            logger.debug(f"Participant {pid}, Session {sid}: excluded (n={n_trials} < {min_valid_trials})")
        else:
            d_score = calculate_d_score(group)
            if np.isnan(d_score):
                status = 'calculation_error'
            else:
                status = 'valid'
        
        results.append({
            'participant_id': pid,
            'session_id': sid,
            'd_score': d_score,
            'n_trials_valid': n_trials,
            'status': status
        })
    
    return pd.DataFrame(results)

def save_aggregated_scores(aggregated_df: pd.DataFrame, output_path: Path) -> None:
    """
    Save aggregated D-scores to a CSV file.
    
    Parameters:
    - aggregated_df: DataFrame with aggregated scores
    - output_path: Path to save the CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aggregated_df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated D-scores to {output_path}")

def main():
    """
    Main entry point for the data processing pipeline.
    This function orchestrates the filtering and aggregation of IAT trials.
    """
    # Example usage (to be replaced by actual CLI or orchestration)
    # This is a placeholder for the main logic that would be called by main.py
    logger.info("Data processing module loaded")

if __name__ == "__main__":
    main()