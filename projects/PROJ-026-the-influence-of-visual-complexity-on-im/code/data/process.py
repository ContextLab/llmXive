"""
Data processing utilities for aggregating raw response logs into D-scores.

Implements Greenwald D2 algorithm, trial filtering, and participant exclusion logic.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from ..data.models import ParticipantResponse, AggregatedScore
import logging
from datetime import datetime
from pathlib import Path
from ..config import get_project_root, get_data_path

logger = logging.getLogger(__name__)

def filter_trials(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter trials based on latency bounds and error handling.
    
    Removes trials with latency < 300ms or > 10000ms, and handles error trials.
    
    Args:
        df: DataFrame containing raw response logs with 'latency' and 'is_error' columns.
        
    Returns:
        Filtered DataFrame.
    """
    if df.empty:
        return df
    
    # Filter by latency bounds
    df = df[(df['latency'] >= 300) & (df['latency'] <= 10000)]
    
    # Remove error trials (is_error == 1 or True)
    if 'is_error' in df.columns:
        df = df[df['is_error'] == 0]
        
    return df.reset_index(drop=True)

def calculate_d_score(df: pd.DataFrame) -> Tuple[float, int]:
    """
    Calculate Greenwald D2 score for a session.
    
    The D2 score is the difference between mean reaction times in two blocks
    divided by the pooled standard deviation.
    
    Args:
        df: Filtered DataFrame for a single session with 'latency' and 'condition' columns.
        
    Returns:
        Tuple of (d_score, n_valid_trials)
    """
    if df.empty:
        return np.nan, 0
        
    # Group by condition (e.g., 'compatible' vs 'incompatible')
    if 'condition' not in df.columns:
        logger.warning("No 'condition' column found, cannot calculate D-score")
        return np.nan, len(df)
        
    groups = df.groupby('condition')['latency']
    
    if len(groups) < 2:
        logger.warning("Less than 2 conditions found, cannot calculate D-score")
        return np.nan, len(df)
        
    means = groups.mean()
    stds = groups.std()
    counts = groups.count()
    
    # Calculate pooled standard deviation
    # D2 = (Mean_Incompatible - Mean_Compatible) / Pooled_SD
    # Pooled_SD = sqrt((SD1^2 + SD2^2) / 2)
    
    if len(means) >= 2:
        # Assuming first two conditions are the ones to compare
        cond_names = list(means.index)
        mean_diff = means.iloc[1] - means.iloc[0]
        
        # Handle cases where std might be NaN (single trial)
        std1 = stds.iloc[0] if not np.isnan(stds.iloc[0]) else 0.0
        std2 = stds.iloc[1] if not np.isnan(stds.iloc[1]) else 0.0
        
        pooled_std = np.sqrt((std1**2 + std2**2) / 2)
        
        if pooled_std == 0:
            d_score = 0.0
        else:
            d_score = mean_diff / pooled_std
            
        return d_score, len(df)
    else:
        return np.nan, len(df)

def aggregate_d_scores(raw_logs: List[pd.DataFrame], participant_ids: List[str], 
                       session_ids: List[str]) -> pd.DataFrame:
    """
    Aggregate raw logs into D-scores per participant/session.
    
    Args:
        raw_logs: List of DataFrames, one per session.
        participant_ids: List of participant IDs corresponding to each log.
        session_ids: List of session IDs corresponding to each log.
        
    Returns:
        DataFrame with columns: participant_id, session_id, d_score, n_trials_valid, status
    """
    results = []
    
    for i, (pid, sid, log_df) in enumerate(zip(participant_ids, session_ids, raw_logs)):
        # Filter trials
        filtered_df = filter_trials(log_df)
        n_valid = len(filtered_df)
        
        # Calculate D-score
        d_score, _ = calculate_d_score(filtered_df)
        
        # Determine status
        if n_valid < 10:
            status = 'excluded_insufficient_trials'
            d_score = np.nan
        elif np.isnan(d_score):
            status = 'error_calculation'
        else:
            status = 'valid'
            
        results.append({
            'participant_id': pid,
            'session_id': sid,
            'd_score': d_score,
            'n_trials_valid': n_valid,
            'status': status
        })
        
    return pd.DataFrame(results)

def load_raw_logs_to_dict(log_dir: Path) -> Dict[str, List[pd.DataFrame]]:
    """
    Load raw response logs from directory into a dictionary.
    
    Args:
        log_dir: Path to directory containing raw log files.
        
    Returns:
        Dictionary mapping participant_id to list of session DataFrames.
    """
    if not log_dir.exists():
        logger.error(f"Log directory not found: {log_dir}")
        return {}
        
    participant_logs = {}
    
    # Assuming files are named like: participantID_sessionID.csv
    for file_path in log_dir.glob("*.csv"):
        try:
            df = pd.read_csv(file_path)
            # Extract participant and session ID from filename or columns
            # Adjust based on actual file naming convention
            stem = file_path.stem
            parts = stem.split('_')
            if len(parts) >= 2:
                pid = parts[0]
                sid = parts[1]
                
                if pid not in participant_logs:
                    participant_logs[pid] = {}
                
                if sid not in participant_logs[pid]:
                    participant_logs[pid][sid] = []
                    
                participant_logs[pid][sid].append(df)
            else:
                logger.warning(f"Could not parse filename: {file_path}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            
    # Flatten to list of (pid, sid, df)
    result_list = []
    for pid, sessions in participant_logs.items():
        for sid, dfs in sessions.items():
            for df in dfs:
                result_list.append((pid, sid, df))
                
    return result_list

def save_aggregated_scores(df: pd.DataFrame, output_path: Path):
    """
    Save aggregated D-scores to CSV.
    
    Args:
        df: DataFrame with aggregated scores.
        output_path: Path to save the CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated scores to {output_path}")

def main():
    """
    Main entry point for aggregating D-scores from raw logs.
    """
    project_root = get_project_root()
    log_dir = get_data_path('raw/responses')
    output_path = get_data_path('processed/aggregated_d_scores.csv')
    
    logging.basicConfig(level=logging.INFO)
    
    logger.info(f"Loading raw logs from {log_dir}")
    raw_data = load_raw_logs_to_dict(log_dir)
    
    if not raw_data:
        logger.warning("No raw logs found. Exiting.")
        return
        
    logger.info(f"Found {len(raw_data)} participants")
    
    # Flatten data
    all_logs = []
    all_pids = []
    all_sids = []
    
    for pid, sessions in raw_data.items():
        for sid, dfs in sessions.items():
            for df in dfs:
                all_logs.append(df)
                all_pids.append(pid)
                all_sids.append(sid)
    
    logger.info(f"Processing {len(all_logs)} sessions")
    
    # Aggregate
    aggregated_df = aggregate_d_scores(all_logs, all_pids, all_sids)
    
    # Save
    save_aggregated_scores(aggregated_df, output_path)
    
    # Print summary
    valid_count = len(aggregated_df[aggregated_df['status'] == 'valid'])
    excluded_count = len(aggregated_df[aggregated_df['status'] == 'excluded_insufficient_trials'])
    logger.info(f"Summary: {valid_count} valid, {excluded_count} excluded")

if __name__ == '__main__':
    main()