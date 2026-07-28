import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import get_project_root, ensure_paths_exist
from utils.io_utils import read_csv, write_csv, ensure_dir

# Constants for edge case handling
EPSILON = 1e-9
WINDOW_SIZE = 20
MIN_SAMPLES_ZSCORE = 5

def load_trajectory_logs(log_dir: Path) -> List[pd.DataFrame]:
    """
    Load all trajectory logs from the specified directory.
    Returns a list of DataFrames, one per trajectory file.
    """
    log_files = list(log_dir.glob("*.csv"))
    if not log_files:
        raise FileNotFoundError(f"No CSV files found in {log_dir}")

    dfs = []
    for file_path in log_files:
        try:
            df = read_csv(file_path)
            # Ensure required columns exist
            required_cols = ['step', 'reward_biased', 'reward_unbiased']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Missing required columns in {file_path}")
            
            # Add seed_id if not present (assume single seed per file for now, or extract from filename)
            if 'seed_id' not in df.columns:
                df['seed_id'] = file_path.stem.split('_')[-1] if '_' in file_path.stem else file_path.stem
            
            if 'bias_type' not in df.columns:
                # Infer from filename or default
                df['bias_type'] = 'unknown'
            
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}", file=sys.stderr)
            raise
    
    return dfs

def compute_divergence_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute G(t) = |J_biased - J_unbiased| per FR-001.
    Assumes input df has 'reward_biased' and 'reward_unbiased' columns.
    """
    df = df.copy()
    df['G_t'] = np.abs(df['reward_biased'] - df['reward_unbiased'])
    return df

def _linear_interpolate_missing(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """
    Perform linear interpolation for missing timesteps in the specified column.
    """
    df = df.copy()
    # Ensure 'step' is integer for interpolation logic
    if df['step'].isnull().any():
        # If steps are missing, we assume they are sequential and fill them
        # This is a simplification; a more robust approach would re-index
        max_step = int(df['step'].max())
        full_index = pd.DataFrame({'step': range(1, max_step + 1)})
        df = full_index.merge(df, on='step', how='left')
    
    # Interpolate the value column
    df[value_col] = df[value_col].interpolate(method='linear')
    return df

def compute_derivative_and_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute dG(t) (discrete derivative) and rolling z-score per FR-002.
    
    Edge Cases:
    - Use linear interpolation for missing timesteps (handled before derivative).
    - If variance of G(t) is zero, set z-score to 0 (using epsilon=1e-9 floor).
    
    Returns DataFrame with 'dG_t' and 'z_score_G' columns.
    """
    df = df.copy()
    
    # 1. Handle missing timesteps via linear interpolation on G_t
    if df['G_t'].isnull().any():
        df = _linear_interpolate_missing(df, 'G_t')
    
    # 2. Compute discrete derivative dG(t) = G(t) - G(t-1)
    # Use diff() which computes x[i] - x[i-1]
    df['dG_t'] = df['G_t'].diff()
    
    # For the first row, diff() is NaN. We can set it to 0 or keep NaN.
    # Per common practice, let's fill the first NaN with 0 (no change from non-existent previous)
    # OR keep it NaN if strictly following "derivative at t=1 is undefined".
    # The prompt says "handle edge cases", usually implying filling. Let's fill with 0.
    df['dG_t'] = df['dG_t'].fillna(0.0)
    
    # 3. Compute Rolling Z-Score for G(t)
    # Z = (x - mean) / std
    # Rolling window size = WINDOW_SIZE, min_periods = MIN_SAMPLES_ZSCORE
    
    rolling_mean = df['G_t'].rolling(window=WINDOW_SIZE, min_periods=MIN_SAMPLES_ZSCORE).mean()
    rolling_std = df['G_t'].rolling(window=WINDOW_SIZE, min_periods=MIN_SAMPLES_ZSCORE).std()
    
    # Handle zero variance: std might be 0 or NaN (if < MIN_SAMPLES)
    # Apply epsilon floor
    rolling_std_safe = np.maximum(rolling_std, EPSILON)
    
    df['z_score_G'] = (df['G_t'] - rolling_mean) / rolling_std_safe
    
    # If rolling_std was originally NaN (insufficient data), z_score should be NaN or 0?
    # If we have < MIN_SAMPLES, we can't compute a meaningful z-score.
    # Let's keep it NaN for the initial period where min_periods isn't met.
    # The calculation above handles the zero-variance case (std=0 -> z=0 if mean matches, or large if not).
    # But if std is NaN (due to < min_samples), the result is NaN.
    
    return df

def process_all_trajectories(logs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Process a list of trajectory DataFrames:
    1. Compute Divergence Gap G(t)
    2. Compute Derivative dG(t) and Z-score
    """
    processed_logs = []
    for df in logs:
        df = compute_divergence_gap(df)
        df = compute_derivative_and_zscore(df)
        processed_logs.append(df)
    return processed_logs

def aggregate_seed_logs(processed_logs: List[pd.DataFrame], output_path: Path) -> None:
    """
    Merge multiple seed logs into a single CSV file.
    Preserves 'seed_id' and 'bias_type' columns.
    """
    if not processed_logs:
        raise ValueError("No processed logs to aggregate")
    
    combined_df = pd.concat(processed_logs, ignore_index=True)
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    write_csv(combined_df, output_path)
    print(f"Aggregated trajectories saved to {output_path}")

def main():
    """
    Main entry point for the ingestion pipeline.
    1. Load logs from data/raw/
    2. Compute G(t), dG(t), z_score_G
    3. Aggregate to data/processed/trajectories_divergence.csv
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    ensure_paths_exist()
    
    if not raw_dir.exists():
        print(f"Error: Raw data directory {raw_dir} does not exist.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading trajectory logs from {raw_dir}...")
    logs = load_trajectory_logs(raw_dir)
    
    print(f"Processing {len(logs)} trajectory logs...")
    processed_logs = process_all_trajectories(logs)
    
    output_file = processed_dir / "trajectories_divergence.csv"
    print(f"Aggregating results to {output_file}...")
    aggregate_seed_logs(processed_logs, output_file)
    
    print("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()