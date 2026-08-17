import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from ..data.models import ParticipantResponse, AggregatedScore
import logging
from datetime import datetime
from pathlib import Path
from ..config import get_project_root

logger = logging.getLogger(__name__)

def filter_trials(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter trials based on latency bounds and error handling.
    
    Thresholds:
    - Remove trials with reaction_time < 300ms
    - Remove trials with reaction_time > 10000ms
    - Remove trials marked as incorrect (is_correct == False)
    
    Args:
        df: DataFrame with raw response logs
        
    Returns:
        Filtered DataFrame
    """
    logger.info(f"Filtering trials: starting with {len(df)} rows")
    
    # Filter by reaction time bounds
    df = df[(df['reaction_time'] >= 300) & (df['reaction_time'] <= 10000)]
    
    # Filter by correctness (keep only correct trials)
    df = df[df['is_correct'] == True]
    
    logger.info(f"Filtering trials: {len(df)} rows remaining")
    return df

def calculate_d_score(df: pd.DataFrame) -> float:
    """
    Calculate Greenwald D2 algorithm for D-score aggregation.
    
    The D2 score is calculated as:
    D = (M_diff) / SD_pooled
    
    Where:
    - M_diff is the mean difference between incompatible and compatible block RTs
    - SD_pooled is the pooled standard deviation of the two blocks
    
    Args:
        df: DataFrame with filtered trials for a single session
        
    Returns:
        D-score value
    """
    if len(df) < 10:
        logger.warning(f"Insufficient trials for D-score calculation: {len(df)}")
        return np.nan
    
    # Separate by block type (assuming session_id encodes block info or we have a block column)
    # For this implementation, we assume the session_id distinguishes the two blocks
    # In a real IAT, we'd have explicit block labels. Here we simulate based on session_id
    
    # If we have two distinct session_ids, treat them as the two conditions
    unique_sessions = df['session_id'].unique()
    if len(unique_sessions) != 2:
        # If only one session, we can't calculate difference
        logger.warning("Cannot calculate D-score: need two conditions")
        return np.nan
    
    block1 = df[df['session_id'] == unique_sessions[0]]['reaction_time']
    block2 = df[df['session_id'] == unique_sessions[1]]['reaction_time']
    
    if len(block1) < 10 or len(block2) < 10:
        logger.warning(f"Insufficient trials in one or both blocks: {len(block1)}, {len(block2)}")
        return np.nan
    
    # Calculate mean difference
    mean_diff = block2.mean() - block1.mean()
    
    # Calculate pooled standard deviation
    n1, n2 = len(block1), len(block2)
    std1, std2 = block1.std(), block2.std()
    
    # Handle zero std
    if std1 == 0 and std2 == 0:
        return np.nan
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return np.nan
    
    d_score = mean_diff / pooled_std
    return d_score

def aggregate_d_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate raw logs into D-scores per participant and session.
    
    Args:
        df: DataFrame with raw response logs
        
    Returns:
        DataFrame with aggregated D-scores
    """
    logger.info(f"Aggregating D-scores for {len(df)} total rows")
    
    # Group by participant_id and session_id
    aggregated = []
    
    for (pid, sid), group in df.groupby(['participant_id', 'session_id']):
        # Filter trials
        filtered = filter_trials(group)
        n_valid = len(filtered)
        
        # Calculate D-score
        d_score = calculate_d_score(filtered)
        
        # Determine status
        if n_valid < 10:
            status = 'insufficient_trials'
            d_score = np.nan
        elif pd.isna(d_score):
            status = 'calculation_failed'
        else:
            status = 'valid'
        
        aggregated.append({
            'participant_id': pid,
            'session_id': sid,
            'd_score': d_score,
            'n_trials_valid': n_valid,
            'status': status
        })
    
    result_df = pd.DataFrame(aggregated)
    logger.info(f"Aggregated {len(result_df)} participant-session combinations")
    
    # Log summary
    valid_count = len(result_df[result_df['status'] == 'valid'])
    logger.info(f"Valid D-scores: {valid_count}/{len(result_df)}")
    
    return result_df

def load_raw_logs_to_dict(data_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Load raw logs from a directory into a dictionary of DataFrames.
    
    Args:
        data_dir: Path to data directory
        
    Returns:
        Dictionary mapping participant_id to their DataFrame
    """
    from .load import load_response_logs
    
    df = load_response_logs(data_dir)
    
    # Group by participant
    participant_logs = {}
    for pid, group in df.groupby('participant_id'):
        participant_logs[pid] = group
    
    return participant_logs

def save_aggregated_scores(df: pd.DataFrame, output_path: str) -> None:
    """
    Save aggregated D-scores to CSV.
    
    Args:
        df: DataFrame with aggregated scores
        output_path: Path to save the CSV
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved aggregated scores to {output_path}")

def main():
    """Main entry point for data processing."""
    import argparse
    from ..config import get_project_root
    
    parser = argparse.ArgumentParser(description='Process response logs to D-scores')
    parser.add_argument('--data-dir', type=str, default=None,
                      help='Path to raw response data directory')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to output CSV file')
    
    args = parser.parse_args()
    root = get_project_root()
    
    data_dir = args.data_dir or str(root / "data" / "raw" / "responses")
    output_path = args.output or str(root / "data" / "processed" / "aggregated_d_scores.csv")
    
    # Load data
    logger.info(f"Loading data from {data_dir}")
    df = load_response_logs(data_dir)
    
    # Aggregate
    aggregated = aggregate_d_scores(df)
    
    # Save
    save_aggregated_scores(aggregated, output_path)
    
    logger.info("Processing complete")

if __name__ == "__main__":
    main()
