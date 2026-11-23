"""
Ingestion module for CHERRL trajectory data.
Computes Divergence Gap G(t), its discrete derivative dG(t),
and rolling z-scores with robust edge case handling.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

from code.config import get_project_root
from code.utils.io_utils import ensure_dir, read_csv, write_csv
from code.utils.math_utils import interpolate_missing_timesteps, safe_z_score, handle_nan

# Constants
ROLLING_WINDOW_SIZE = 20
MIN_SAMPLES_FOR_ZSCORE = 5
ZSCORE_EPSILON = 1e-9


def load_trajectory_logs(logs_dir: Path) -> List[pd.DataFrame]:
    """
    Load all trajectory CSV logs from the specified directory.
    Returns a list of DataFrames, one per seed log file.
    """
    if not logs_dir.exists():
        raise FileNotFoundError(f"Logs directory not found: {logs_dir}")

    log_files = list(logs_dir.glob("*.csv"))
    if not log_files:
        raise ValueError(f"No CSV files found in {logs_dir}")

    trajectories = []
    for log_file in log_files:
        # Extract seed_id from filename if possible, otherwise use index
        seed_id = log_file.stem
        try:
            df = read_csv(log_file)
            # Ensure required columns exist
            required_cols = ['timestep', 'J_biased', 'J_unbiased', 'J_gold']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                raise ValueError(f"Missing columns in {log_file}: {missing}")
            
            df['seed_id'] = seed_id
            trajectories.append(df)
        except Exception as e:
            print(f"Warning: Failed to load {log_file}: {e}", file=sys.stderr)
            continue

    if not trajectories:
        raise RuntimeError("No valid trajectory files could be loaded.")

    return trajectories


def compute_divergence_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute G(t) = |J_biased - J_unbiased| for each timestep.
    """
    df = df.copy()
    # Ensure numeric types
    df['J_biased'] = pd.to_numeric(df['J_biased'], errors='coerce')
    df['J_unbiased'] = pd.to_numeric(df['J_unbiased'], errors='coerce')
    
    # Compute G(t)
    df['G_t'] = (df['J_biased'] - df['J_unbiased']).abs()
    
    return df


def compute_derivative_and_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute discrete derivative dG(t) = G(t) - G(t-1) and rolling z-score.
    Uses linear interpolation for missing timesteps and safe z-score calculation.
    
    Logic:
    1. Interpolate missing timesteps using linear interpolation (T017).
    2. Compute discrete derivative dG(t).
    3. Compute rolling z-score with window W=20, min_samples=5.
       - If variance is zero, z-score is 0 (using epsilon floor).
    """
    df = df.copy()
    
    # 1. Interpolate missing timesteps
    # Ensure sorted by timestep
    df = df.sort_values('timestep').reset_index(drop=True)
    df = interpolate_missing_timesteps(df, 'timestep', ['G_t'])
    
    # 2. Compute discrete derivative dG(t) = G(t) - G(t-1)
    # Shift G_t by 1 to get G(t-1)
    G_t_lag = df['G_t'].shift(1)
    # dG(t) = G(t) - G(t-1)
    df['dG_t'] = df['G_t'] - G_t_lag
    
    # Handle NaN in dG_t (first row will be NaN)
    # We can leave the first row as NaN or fill with 0. 
    # Standard practice for derivative is NaN at start.
    
    # 3. Compute rolling z-score for G_t
    # z-score = (x - mean) / std
    # Rolling window: W=20, min_samples=5
    
    def rolling_zscore(series: pd.Series, window: int, min_samples: int, epsilon: float) -> pd.Series:
        """
        Compute rolling z-score with safe division and min_samples constraint.
        """
        results = []
        for i in range(len(series)):
            start_idx = max(0, i - window + 1)
            window_data = series.iloc[start_idx:i+1]
            
            if len(window_data) < min_samples:
                # Not enough samples, return NaN or handle as per spec
                # Spec says "requiring a minimum of 5 samples to compute"
                results.append(np.nan)
                continue
            
            mean_val = window_data.mean()
            std_val = window_data.std(ddof=0) # Population std for rolling window typically
            
            # Safe z-score calculation
            if std_val < epsilon:
                z = 0.0
            else:
                z = (series.iloc[i] - mean_val) / std_val
            
            results.append(z)
        
        return pd.Series(results, index=series.index)
    
    # Apply rolling z-score to G_t
    df['z_G_t'] = rolling_zscore(df['G_t'], ROLLING_WINDOW_SIZE, MIN_SAMPLES_FOR_ZSCORE, ZSCORE_EPSILON)
    
    # Handle any remaining NaNs in G_t or dG_t if they exist (though interpolation should fix gaps)
    df['G_t'] = handle_nan(df['G_t'])
    df['dG_t'] = handle_nan(df['dG_t'])
    
    return df


def process_all_trajectories(trajectories: List[pd.DataFrame]) -> List[pd.DataFrame]:
    """
    Process a list of trajectory DataFrames: compute G(t), dG(t), and z-scores.
    """
    processed = []
    for df in trajectories:
        df = compute_divergence_gap(df)
        df = compute_derivative_and_zscore(df)
        processed.append(df)
    return processed


def aggregate_seed_logs(processed_trajectories: List[pd.DataFrame], output_path: Path) -> pd.DataFrame:
    """
    Aggregate all processed trajectory DataFrames into a single CSV.
    Output schema: seed_id, bias_type, timestep, J_biased, J_unbiased, J_gold, G_t, dG_t, z_G_t
    """
    if not processed_trajectories:
        raise ValueError("No trajectories to aggregate.")
    
    # Concatenate all DataFrames
    combined_df = pd.concat(processed_trajectories, ignore_index=True)
    
    # Ensure correct column order
    # Note: bias_type might not be in the raw logs, check if it exists
    cols_to_keep = ['seed_id', 'bias_type', 'timestep', 'J_biased', 'J_unbiased', 'J_gold', 'G_t', 'dG_t', 'z_G_t']
    # Filter to only existing columns
    existing_cols = [c for c in cols_to_keep if c in combined_df.columns]
    
    final_df = combined_df[existing_cols]
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    # Write to CSV
    write_csv(final_df, output_path)
    
    print(f"Aggregated trajectories saved to {output_path}")
    return final_df


def main():
    """
    Main entry point for the ingestion pipeline.
    1. Load raw logs from data/raw/cherrl_logs/
    2. Compute G(t), dG(t), z-score
    3. Aggregate to data/processed/trajectories_divergence.csv
    """
    root = get_project_root()
    logs_dir = root / "data" / "raw" / "cherrl_logs"
    output_file = root / "data" / "processed" / "trajectories_divergence.csv"
    
    print("Starting ingestion pipeline...")
    
    # Load logs
    try:
        trajectories = load_trajectory_logs(logs_dir)
        print(f"Loaded {len(trajectories)} trajectory files.")
    except Exception as e:
        print(f"ERROR: Failed to load trajectory logs: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Process
    processed = process_all_trajectories(trajectories)
    print(f"Processed {len(processed)} trajectories.")
    
    # Aggregate
    try:
        aggregate_seed_logs(processed, output_file)
    except Exception as e:
        print(f"ERROR: Failed to aggregate trajectories: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Ingestion pipeline completed successfully.")


if __name__ == "__main__":
    main()