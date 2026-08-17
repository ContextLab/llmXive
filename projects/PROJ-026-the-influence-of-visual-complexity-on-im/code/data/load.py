import argparse
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional
import logging
import numpy as np
from ..config import get_project_root, SEED
from ..utils.logging import get_logger

logger = get_logger(__name__)

def load_response_logs(data_dir: str) -> pd.DataFrame:
    """
    Load raw response logs from a directory.
    
    Args:
        data_dir: Path to the directory containing response logs
        
    Returns:
        DataFrame with response data
        
    Raises:
        RuntimeError: If data is synthetic in production mode
        FileNotFoundError: If no data files are found
    """
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Data directory not found: {root}")
    
    # Look for CSV files
    csv_files = list(root.glob('*.csv'))
    
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {root}")
    
    # Load and concatenate all CSV files
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
            logger.info(f"Loaded {len(df)} rows from {csv_file.name}")
        except Exception as e:
            logger.error(f"Failed to load {csv_file.name}: {e}")
            continue
    
    if not dfs:
        raise ValueError("No valid data files could be loaded")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total rows loaded: {len(combined_df)}")
    
    # Validate expected columns
    required_cols = {'participant_id', 'session_id', 'reaction_time', 'is_correct'}
    if not required_cols.issubset(combined_df.columns):
        missing = required_cols - set(combined_df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    return combined_df

def generate_synthetic_response_logs(n_participants: int = 100, n_trials: int = 40, seed: int = SEED) -> pd.DataFrame:
    """
    Generate synthetic response logs for CI/testing.
    
    Args:
        n_participants: Number of participants
        n_trials: Number of trials per participant
        seed: Random seed
        
    Returns:
        DataFrame with synthetic response data
    """
    np.random.seed(seed)
    
    participant_ids = [f"P{i:03d}" for i in range(n_participants)]
    sessions = ['session_1', 'session_2']
    
    data = []
    for pid in participant_ids:
        for session in sessions:
            for trial in range(n_trials):
                # Generate synthetic reaction times (normal distribution)
                rt = np.random.normal(600, 150)
                rt = np.clip(rt, 200, 2000)  # Clamp to realistic range
                
                # Generate correctness (80% accuracy)
                is_correct = np.random.random() < 0.8
                
                data.append({
                    'participant_id': pid,
                    'session_id': session,
                    'trial_id': trial,
                    'reaction_time': rt,
                    'is_correct': is_correct,
                    'timestamp': pd.Timestamp.now()
                })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} synthetic response records")
    return df

def main():
    """Main entry point for data loading."""
    parser = argparse.ArgumentParser(description='Load response logs')
    parser.add_argument('--null-effect', action='store_true', 
                      help='Generate synthetic data for CI/testing')
    parser.add_argument('--data-dir', type=str, default=None,
                      help='Path to data directory')
    
    args = parser.parse_args()
    root = get_project_root()
    
    if args.null_effect:
        logger.info("Generating synthetic data in null-effect mode")
        df = generate_synthetic_response_logs()
        output_path = root / "data" / "raw" / "responses" / "synthetic_responses.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved synthetic data to {output_path}")
    else:
        data_dir = args.data_dir or str(root / "data" / "raw" / "responses")
        if not Path(data_dir).exists() or not list(Path(data_dir).glob('*.csv')):
            raise RuntimeError(
                "Production mode active but no real data found. "
                "Please provide real response logs or use --null-effect for CI."
            )
        df = load_response_logs(data_dir)
        logger.info(f"Loaded real data from {data_dir}")

if __name__ == "__main__":
    main()
