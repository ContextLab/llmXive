import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import get_project_root
from utils.io_utils import read_csv, write_csv, ensure_dir
from utils.math_utils import interpolate_missing_timesteps, safe_z_score, rolling_std_dev

# Constants for FR-002
ROLLING_WINDOW_SIZE = 20
MIN_SAMPLES_FOR_STD = 5
EPSILON_FLOOR = 1e-9

def load_trajectory_logs(log_dir: Path) -> List[pd.DataFrame]:
    """
    Load all trajectory CSV logs from the specified directory.
    Returns a list of DataFrames, one per seed log.
    """
    log_files = list(log_dir.glob("*.csv"))
    if not log_files:
        raise FileNotFoundError(f"No CSV files found in {log_dir}")

    dfs = []
    for f_path in log_files:
        try:
            df = read_csv(f_path)
            # Ensure required columns exist
            required_cols = ['timestep', 'J_biased', 'J_unbiased', 'J_gold']
            if not all(col in df.columns for col in required_cols):
                # Try to infer if columns are named differently or missing
                # For now, strict adherence to spec
                raise ValueError(f"File {f_path} missing required columns: {required_cols}")
            
            # Add seed_id based on filename if not present
            seed_id = f_path.stem
            df['seed_id'] = seed_id
            
            # Infer bias_type if not present (placeholder logic, assumes filename pattern or default)
            # In a real scenario, this might be parsed from filename or metadata
            if 'bias_type' not in df.columns:
                df['bias_type'] = 'unknown' 
            
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Failed to load {f_path}: {e}", file=sys.stderr)
            continue
    
    return dfs

def compute_divergence_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute G(t) = |J_biased - J_unbiased| as per FR-001.
    """
    if 'G_t' not in df.columns:
        df['G_t'] = (df['J_biased'] - df['J_unbiased']).abs()
    return df

def compute_derivative_and_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute dG(t) (discrete derivative) and rolling z-score for G(t).
    
    Logic per T015:
    1. Compute dG(t) = G(t) - G(t-1).
    2. Use linear interpolation for missing timesteps (T017).
    3. Calculate rolling z-score with window W=20, min_samples=5.
    4. If variance is zero, z-score = 0 (using epsilon floor).
    """
    if df.empty:
        return df

    # Ensure sorted by timestep
    df = df.sort_values('timestep').reset_index(drop=True)

    # 1. Handle missing timesteps via interpolation (T017 dependency)
    # We interpolate numeric columns to fill gaps in the time series
    numeric_cols = ['J_biased', 'J_unbiased', 'J_gold']
    # Check if G_t exists, if not compute it first
    if 'G_t' not in df.columns:
        df = compute_divergence_gap(df)
    
    cols_to_interp = numeric_cols + ['G_t']
    df = interpolate_missing_timesteps(df, cols_to_interp)

    # 2. Compute Discrete Derivative dG(t)
    # dG(t) = G(t) - G(t-1)
    df['dG_t'] = df['G_t'].diff()
    
    # 3. Compute Rolling Z-Score for G(t)
    # Window size W=20, min_samples=5
    # z(t) = (G(t) - rolling_mean) / rolling_std
    
    # Calculate rolling mean
    rolling_mean = df['G_t'].rolling(
        window=ROLLING_WINDOW_SIZE, 
        min_periods=MIN_SAMPLES_FOR_STD
    ).mean()

    # Calculate rolling std with epsilon floor logic handled inside safe_z_score or here
    # rolling_std_dev utility from math_utils expects a series and window
    # We need to ensure it uses min_periods=5
    
    # Using the utility function from math_utils for rolling std
    # Note: rolling_std_dev in math_utils likely takes the series and window
    rolling_std = rolling_std_dev(df['G_t'], ROLLING_WINDOW_SIZE, min_samples=MIN_SAMPLES_FOR_STD)
    
    # Apply safe_z_score which handles zero variance
    df['z_score'] = safe_z_score(df['G_t'], rolling_mean, rolling_std, epsilon=EPSILON_FLOOR)

    return df

def process_all_trajectories(log_dir: Path) -> pd.DataFrame:
    """
    Process all trajectory logs: load, compute G(t), dG(t), and z-score.
    Returns a combined DataFrame.
    """
    log_files = list(log_dir.glob("*.csv"))
    if not log_files:
        raise FileNotFoundError(f"No CSV files found in {log_dir}")

    processed_dfs = []
    for f_path in log_files:
        try:
            df = read_csv(f_path)
            # Add seed_id
            df['seed_id'] = f_path.stem
            if 'bias_type' not in df.columns:
                df['bias_type'] = 'unknown' # Default if missing
            
            # Compute metrics
            df = compute_divergence_gap(df)
            df = compute_derivative_and_zscore(df)
            
            processed_dfs.append(df)
        except Exception as e:
            print(f"Error processing {f_path}: {e}", file=sys.stderr)
            continue

    if not processed_dfs:
        raise RuntimeError("No trajectories were successfully processed.")

    return pd.concat(processed_dfs, ignore_index=True)

def aggregate_seed_logs(processed_df: pd.DataFrame, output_path: Path) -> None:
    """
    Aggregate processed trajectories into a single CSV file.
    Output columns: seed_id, bias_type, timestep, J_biased, J_unbiased, J_gold, G_t, dG_t, z_score
    """
    ensure_dir(output_path.parent)
    
    # Select and order columns as per spec
    cols = ['seed_id', 'bias_type', 'timestep', 'J_biased', 'J_unbiased', 'J_gold', 'G_t', 'dG_t', 'z_score']
    
    # Filter to only existing columns in case some are missing (though they should be present)
    final_cols = [c for c in cols if c in processed_df.columns]
    
    result_df = processed_df[final_cols]
    
    # Sort by seed_id and timestep for consistent output
    result_df = result_df.sort_values(['seed_id', 'timestep'])
    
    write_csv(result_df, output_path)
    print(f"Aggregated data saved to {output_path}")

def main():
    """
    Main entry point for T015 execution.
    Reads from data/raw/cherrl_logs/ and writes to data/processed/trajectories_divergence.csv
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw" / "cherrl_logs"
    output_file = project_root / "data" / "processed" / "trajectories_divergence.csv"

    if not raw_dir.exists():
        print(f"Error: Raw data directory not found: {raw_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing trajectories from {raw_dir}...")
    
    try:
        # Process all logs
        combined_df = process_all_trajectories(raw_dir)
        
        # Aggregate and save
        aggregate_seed_logs(combined_df, output_file)
        
        print("T015 completed successfully.")
    except Exception as e:
        print(f"Error during T015 execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()