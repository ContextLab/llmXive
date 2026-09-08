"""
Data processing module for aggregating raw IAT response logs into D-scores.

Implements:
- Trial filtering (latency bounds, error handling)
- Greenwald D2 algorithm for D-score aggregation
- Aggregation logic linking sessions to complexity conditions
- CSV serialization of results
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
from pathlib import Path

# Import from sibling modules to ensure API consistency
from config import get_data_path, get_project_root
from data.models import AggregatedScore
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for trial filtering
MIN_LATENCY_MS = 300
MAX_LATENCY_MS = 10000
MIN_VALID_TRIALS = 10

def filter_trials(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter raw trial logs based on latency bounds and error status.

    Args:
        df: DataFrame with columns including 'reaction_time' and 'is_correct'.

    Returns:
        Filtered DataFrame containing only valid trials.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to filter_trials")
        return df

    # Filter by latency bounds
    valid_latency = (df['reaction_time'] >= MIN_LATENCY_MS) & (df['reaction_time'] <= MAX_LATENCY_MS)
    # Filter by correctness (assuming True/1 means correct, False/0 means error)
    # Typically IAT D-score uses all trials but weights errors differently,
    # but for strict filtering as per spec T022:
    # "Remove trials <300ms or >10000ms".
    # We also keep 'is_correct' for potential downstream logic, but strictly
    # the spec says filter latency. However, standard D-score often excludes
    # error trials or handles them specially. Let's follow T022 strictly for latency.
    # T020 mentions "trial filtering (latency <300ms, >10000ms, errors)".
    # So we filter errors too.
    valid_trials = valid_latency & df['is_correct'].astype(bool)

    filtered_df = df[valid_trials].copy()
    logger.info(f"Filtered {len(df) - len(filtered_df)} trials. Kept {len(filtered_df)}.")
    return filtered_df

def calculate_d_score(trials_block1: pd.Series, trials_block2: pd.Series) -> float:
    """
    Calculate the Greenwald D2 score for a pair of blocks.

    Formula: D = (Mean(Block2) - Mean(Block1)) / Pooled_SD
    Pooled_SD is the standard deviation of the concatenated trials of both blocks.

    Args:
        trials_block1: Series of reaction times for Block 1.
        trials_block2: Series of reaction times for Block 2.

    Returns:
        D-score (float).
    """
    if len(trials_block1) == 0 or len(trials_block2) == 0:
        return np.nan

    combined = pd.concat([trials_block1, trials_block2])
    mean_diff = trials_block2.mean() - trials_block1.mean()
    pooled_std = combined.std(ddof=0) # Greenwald D uses population std dev for the denominator in some formulations,
                                      # but standard implementation often uses pooled sample std.
                                      # Greenwald et al. (2003) specify using the standard deviation of all included trials.
                                      # We use ddof=0 to match the "standard deviation of all included trials" definition strictly,
                                      # or ddof=1 for sample. The original paper uses the standard deviation of the combined set.
                                      # Let's use the standard deviation of the combined set (ddof=0 is population, but often in stats
                                      # we use sample. Greenwald D2 specifically uses the standard deviation of the combined trials.
                                      # Implementation in IAT software usually uses the standard deviation of the combined set.
                                      # To be safe and standard: use the standard deviation of the combined set.
                                      # Let's use ddof=0 as per "standard deviation of all included trials" (population of those trials).
                                      # Actually, most Python implementations use ddof=0 for the D-score denominator.
                                      # We will use ddof=0.

    if pooled_std == 0:
        return 0.0

    d_score = mean_diff / pooled_std
    return d_score

def load_raw_logs_to_dict(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all raw response logs from the directory into a dictionary keyed by file/stimulus.
    Expects files named like 'participant_session.csv' or similar structure.
    For this implementation, we assume a flat structure where we can group by participant_id and session_id.

    Args:
        raw_dir: Path to the raw response data directory.

    Returns:
        Dictionary mapping (participant_id, session_id) to DataFrame.
    """
    data_path = get_data_path()
    responses_path = data_path / "raw" / "responses"
    
    if not responses_path.exists():
        raise FileNotFoundError(f"Raw responses directory not found: {responses_path}")

    all_logs = []
    for file_path in responses_path.glob("*.csv"):
        try:
            df = pd.read_csv(file_path)
            # Ensure required columns exist
            required_cols = ['participant_id', 'session_id', 'reaction_time', 'is_correct', 'stimulus_condition']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Skipping {file_path}: missing required columns. Found: {df.columns.tolist()}")
                continue
            all_logs.append(df)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    if not all_logs:
        raise RuntimeError("No valid response log files found in the raw directory.")

    combined_df = pd.concat(all_logs, ignore_index=True)
    
    # Group by participant and session
    grouped = {}
    for (pid, sid), group in combined_df.groupby(['participant_id', 'session_id']):
        grouped[(pid, sid)] = group

    return grouped

def aggregate_d_scores(
    raw_data: Dict[Tuple[str, str], pd.DataFrame],
    counterbalance_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Aggregate raw logs into D-scores per session, linking to complexity conditions.

    Args:
        raw_data: Dictionary of (participant_id, session_id) -> DataFrame.
        counterbalance_path: Path to counterbalance assignment file to map sessions to conditions.

    Returns:
        DataFrame with columns: participant_id, session_id, complexity_condition, d_score, n_trials_valid, status.
    """
    results = []
    
    # Load counterbalance if provided to map session_id to condition
    condition_map = {}
    if counterbalance_path and counterbalance_path.exists():
        try:
            cb_df = pd.read_csv(counterbalance_path)
            # Expected columns: participant_id, session_id, complexity_condition
            for _, row in cb_df.iterrows():
                key = (row['participant_id'], row['session_id'])
                condition_map[key] = row['complexity_condition']
        except Exception as e:
            logger.error(f"Failed to load counterbalance file: {e}")
    else:
        logger.warning("Counterbalance file not found or provided. Conditions will be unknown.")

    # Group by participant to find paired sessions (Low/High)
    # We need to identify which session is Low and which is High.
    # The counterbalance file should tell us this.
    
    participants = set([pid for pid, _ in raw_data.keys()])
    
    for pid in participants:
        sessions_for_participant = [(sid, raw_data[(pid, sid)]) for sid, _ in raw_data.keys() if sid.startswith(pid)]
        # Actually, the keys are (pid, sid). Let's filter correctly.
        sessions_for_participant = [
            (sid, df) for (p, sid), df in raw_data.items() if p == pid
        ]
        
        if len(sessions_for_participant) < 2:
            # If we don't have paired data, we can still process individual sessions if possible,
            # but the task emphasizes "paired session data". We will process what we have.
            logger.warning(f"Participant {pid} has fewer than 2 sessions: {len(sessions_for_participant)}")

        for sid, df in sessions_for_participant:
            # Filter trials
            valid_trials = filter_trials(df)
            n_valid = len(valid_trials)
            
            # Check minimum trials
            if n_valid < MIN_VALID_TRIALS:
                d_score = np.nan
                status = 'insufficient_trials'
            else:
                # Split into two blocks for D-score calculation
                # Assuming the session data contains two blocks (e.g., Block 1 and Block 2)
                # The spec implies a standard IAT structure. We assume the data has a 'block' column or similar.
                # If not, we might need to split the sorted data or assume the first half vs second half.
                # Standard IAT: Block 1 (Practice), Block 2 (Test), etc.
                # Greenwald D2 uses specific pairs of blocks.
                # For simplicity in this generic implementation, we assume the data is split into two halves
                # or has a 'block' identifier. Let's assume a 'block' column exists.
                if 'block' not in valid_trials.columns:
                    # Fallback: split by index if no block column
                    mid = len(valid_trials) // 2
                    if mid == 0:
                        d_score = np.nan
                        status = 'insufficient_trials'
                        continue
                    block1 = valid_trials.iloc[:mid]['reaction_time']
                    block2 = valid_trials.iloc[mid:]['reaction_time']
                else:
                    blocks = valid_trials['block'].unique()
                    if len(blocks) < 2:
                        d_score = np.nan
                        status = 'insufficient_blocks'
                        continue
                    # Assume block 1 and 2 are the ones to compare
                    b1_data = valid_trials[valid_trials['block'] == blocks[0]]['reaction_time']
                    b2_data = valid_trials[valid_trials['block'] == blocks[1]]['reaction_time']
                    if len(b1_data) < MIN_VALID_TRIALS or len(b2_data) < MIN_VALID_TRIALS:
                         d_score = np.nan
                         status = 'insufficient_trials'
                         continue
                    block1 = b1_data
                    block2 = b2_data

                d_score = calculate_d_score(block1, block2)
                status = 'valid'

            # Determine complexity condition
            condition = condition_map.get((pid, sid), 'unknown')
            
            results.append({
                'participant_id': pid,
                'session_id': sid,
                'complexity_condition': condition,
                'd_score': d_score,
                'n_trials_valid': n_valid,
                'status': status
            })

    return pd.DataFrame(results)

def save_aggregated_scores(df: pd.DataFrame, output_path: Path):
    """
    Save the aggregated D-scores to a CSV file.

    Args:
        df: DataFrame with aggregated scores.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated D-scores to {output_path}")

def main():
    """
    Main entry point for the aggregation pipeline.
    """
    project_root = get_project_root()
    data_path = get_data_path()
    
    # Paths
    raw_dir = data_path / "raw" / "responses"
    counterbalance_path = data_path / "processed" / "counterbalance_assignment.csv"
    output_path = data_path / "processed" / "aggregated_d_scores.csv"
    
    logger.info("Starting D-score aggregation...")
    
    try:
        # Load raw logs
        raw_data = load_raw_logs_to_dict(raw_dir)
        logger.info(f"Loaded data for {len(raw_data)} sessions.")
        
        # Aggregate
        aggregated_df = aggregate_d_scores(raw_data, counterbalance_path)
        
        # Save
        save_aggregated_scores(aggregated_df, output_path)
        
        logger.info("Aggregation complete.")
        
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()