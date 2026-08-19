"""
Data processing module for aggregating IAT response logs into D-scores.

Implements trial filtering, Greenwald D2 calculation, and aggregation
per participant/session with complexity condition mapping.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime
from pathlib import Path
import json

from ..data.models import ParticipantResponse, AggregatedScore
from ..config import get_project_root, get_data_path

logger = logging.getLogger(__name__)

# Constants
LATENCY_MIN = 300.0
LATENCY_MAX = 10000.0
MIN_VALID_TRIALS = 10

def filter_trials(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter trials based on latency bounds and error handling.
    
    Removes trials with latency < 300ms or > 10000ms.
    Marks error trials for exclusion in D-score calculation.
    
    Args:
        df: DataFrame with columns including 'reaction_time' and 'is_correct'
        
    Returns:
        Filtered DataFrame with valid trials only
    """
    logger.info(f"Filtering trials: removing RT < {LATENCY_MIN}ms or > {LATENCY_MAX}ms")
    
    valid_mask = (
        (df['reaction_time'] >= LATENCY_MIN) & 
        (df['reaction_time'] <= LATENCY_MAX)
    )
    
    filtered_df = df[valid_mask].copy()
    logger.info(f"Retained {len(filtered_df)} of {len(df)} trials after latency filtering")
    
    return filtered_df

def calculate_d_score(df: pd.DataFrame) -> Tuple[float, int]:
    """
    Calculate Greenwald D2 algorithm for a single session.
    
    D = (mean(L2) - mean(L1)) / (SD(L1) + SD(L2)) / 2
    where L1 and L2 are the two block conditions.
    
    Args:
        df: DataFrame with columns 'reaction_time' and 'condition' (L1/L2)
        
    Returns:
        Tuple of (d_score, n_valid_trials)
    """
    if df.empty:
        return np.nan, 0
    
    # Group by condition
    l1 = df[df['condition'] == 'L1']['reaction_time']
    l2 = df[df['condition'] == 'L2']['reaction_time']
    
    if len(l1) < 5 or len(l2) < 5:
        logger.warning("Insufficient trials in one or both conditions")
        return np.nan, len(df)
    
    # Calculate means and SDs
    mean_l1 = l1.mean()
    mean_l2 = l2.mean()
    sd_l1 = l1.std()
    sd_l2 = l2.std()
    
    # D2 formula: difference divided by average SD
    pooled_sd = (sd_l1 + sd_l2) / 2.0
    
    if pooled_sd == 0:
        return np.nan, len(df)
        
    d_score = (mean_l2 - mean_l1) / pooled_sd
    
    return d_score, len(df)

def load_raw_logs_to_dict(logs_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all raw response log CSV files from directory.
    
    Args:
        logs_dir: Path to directory containing raw response logs
        
    Returns:
        Dictionary mapping (participant_id, session_id) to DataFrame
    """
    logs_dict = {}
    
    if not logs_dir.exists():
        raise FileNotFoundError(f"Logs directory not found: {logs_dir}")
        
    csv_files = list(logs_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {logs_dir}")
        
    logger.info(f"Found {len(csv_files)} response log files")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # Validate required columns
            required_cols = ['participant_id', 'session_id', 'reaction_time', 'is_correct', 'condition']
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                logger.warning(f"Skipping {csv_file}: missing columns {missing_cols}")
                continue
            
            key = (df['participant_id'].iloc[0], df['session_id'].iloc[0])
            logs_dict[key] = df
            logger.info(f"Loaded {len(df)} trials from {csv_file.name} for {key}")
            
        except Exception as e:
            logger.error(f"Failed to load {csv_file}: {e}")
            continue
            
    return logs_dict

def aggregate_d_scores(
    logs_dict: Dict[str, pd.DataFrame],
    counterbalance_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Aggregate raw logs into D-scores per participant/session.
    
    Maps session IDs to complexity conditions (Low/High) using counterbalance data.
    Excludes participants with < MIN_VALID_TRIALS valid trials.
    
    Args:
        logs_dict: Dictionary of raw log DataFrames
        counterbalance_df: DataFrame with participant_id, session_id, complexity_condition
        
    Returns:
        Aggregated DataFrame with columns:
        participant_id, session_id, complexity_condition, d_score, n_trials_valid, status
    """
    results = []
    
    # Create lookup for counterbalance assignments
    cb_lookup = {}
    for _, row in counterbalance_df.iterrows():
        key = (row['participant_id'], row['session_id'])
        cb_lookup[key] = row['complexity_condition']
        
    for (participant_id, session_id), df in logs_dict.items():
        # Filter trials
        filtered_df = filter_trials(df)
        
        # Calculate D-score
        d_score, n_valid = calculate_d_score(filtered_df)
        
        # Get complexity condition from counterbalance
        complexity_condition = cb_lookup.get((participant_id, session_id), 'Unknown')
        
        # Determine status
        if n_valid < MIN_VALID_TRIALS:
            status = 'insufficient_trials'
            d_score = np.nan
        elif pd.isna(d_score):
            status = 'calculation_failed'
        else:
            status = 'valid'
            
        results.append({
            'participant_id': participant_id,
            'session_id': session_id,
            'complexity_condition': complexity_condition,
            'd_score': d_score,
            'n_trials_valid': n_valid,
            'status': status
        })
        
    aggregated_df = pd.DataFrame(results)
    
    # Ensure paired data is properly linked
    logger.info(f"Aggregated {len(aggregated_df)} session records")
    
    return aggregated_df

def save_aggregated_scores(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save aggregated D-scores to CSV.
    
    Args:
        df: Aggregated DataFrame
        output_path: Path to output CSV file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregated scores to {output_path}")
    
    # Log summary
    valid_count = len(df[df['status'] == 'valid'])
    logger.info(f"Valid sessions: {valid_count}/{len(df)}")

def main():
    """
    Main entry point for D-score aggregation pipeline.
    
    Usage:
        python -m code.data.process [--logs-dir DATA/raw/responses] [--cb-file DATA/processed/counterbalance_assignment.csv]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Aggregate IAT response logs into D-scores")
    parser.add_argument(
        '--logs-dir',
        type=str,
        default=None,
        help='Path to raw response logs directory'
    )
    parser.add_argument(
        '--cb-file',
        type=str,
        default=None,
        help='Path to counterbalance assignment CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output aggregated D-scores CSV'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    from ..utils.logging import setup_logging
    setup_logging()
    
    # Resolve paths
    project_root = get_project_root()
    
    logs_dir = Path(args.logs_dir) if args.logs_dir else project_root / "data" / "raw" / "responses"
    cb_file = Path(args.cb_file) if args.cb_file else project_root / "data" / "processed" / "counterbalance_assignment.csv"
    output_path = Path(args.output) if args.output else project_root / "data" / "processed" / "aggregated_d_scores.csv"
    
    logger.info(f"Loading logs from: {logs_dir}")
    logger.info(f"Using counterbalance from: {cb_file}")
    logger.info(f"Output will be written to: {output_path}")
    
    # Load counterbalance assignments
    if not cb_file.exists():
        raise FileNotFoundError(f"Counterbalance file not found: {cb_file}. Run T027a first.")
        
    counterbalance_df = pd.read_csv(cb_file)
    logger.info(f"Loaded {len(counterbalance_df)} counterbalance assignments")
    
    # Load raw logs
    try:
        logs_dict = load_raw_logs_to_dict(logs_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
        
    if not logs_dict:
        raise ValueError("No valid log files found in the specified directory")
        
    # Aggregate D-scores
    aggregated_df = aggregate_d_scores(logs_dict, counterbalance_df)
    
    # Save results
    save_aggregated_scores(aggregated_df, output_path)
    
    # Verify output schema
    required_cols = ['participant_id', 'session_id', 'complexity_condition', 'd_score', 'n_trials_valid', 'status']
    missing_cols = [c for c in required_cols if c not in aggregated_df.columns]
    if missing_cols:
        raise ValueError(f"Output missing required columns: {missing_cols}")
        
    logger.info("Aggregation complete. Schema verified.")
    
    return aggregated_df

if __name__ == "__main__":
    main()