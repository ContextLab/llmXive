import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from code.config import get_project_root
from code.utils.io_utils import read_csv, write_csv, ensure_dir

def load_trajectory_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all trajectory CSV logs from the specified directory.
    Expects files named like `seed_*.csv` containing columns:
    ['step', 't', 'J_biased', 'J_unbiased', 'J_gold', 'bias_type', 'seed_id']
    """
    logs = []
    if not log_dir.exists():
        raise FileNotFoundError(f"Log directory not found: {log_dir}")
    
    for file_path in sorted(log_dir.glob("*.csv")):
        try:
            df = pd.read_csv(file_path)
            required_cols = {'step', 't', 'J_biased', 'J_unbiased', 'J_gold'}
            if not required_cols.issubset(df.columns):
                missing = required_cols - set(df.columns)
                raise ValueError(f"File {file_path.name} missing columns: {missing}")
            
            # Ensure numeric types
            numeric_cols = ['step', 't', 'J_biased', 'J_unbiased', 'J_gold']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Infer metadata from filename if not present
            if 'seed_id' not in df.columns:
                df['seed_id'] = file_path.stem.replace('seed_', '')
            if 'bias_type' not in df.columns:
                df['bias_type'] = 'unknown'
                
            logs.append(df)
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)
    
    return logs

def compute_divergence_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute G(t) = |J_biased - J_unbiased| (FR-001).
    """
    if 'J_biased' not in df.columns or 'J_unbiased' not in df.columns:
        raise ValueError("Input DataFrame must contain 'J_biased' and 'J_unbiased' columns.")
    
    df = df.copy()
    df['G_t'] = (df['J_biased'] - df['J_unbiased']).abs()
    return df

def compute_derivative_and_zscore(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Compute dG(t) (discrete derivative) and rolling z-score.
    Implements edge case handling for zero-variance and missing timesteps.
    
    - Missing timesteps (NaN in G_t): Interpolate linearly if possible, otherwise skip in derivative.
    - Zero-variance G(t) within window: Set z-score to 0.
    """
    if 'G_t' not in df.columns:
        raise ValueError("Input DataFrame must contain 'G_t' column.")
    
    df = df.copy()
    
    # 1. Handle missing timesteps (interpolation)
    # Sort by step to ensure correct order
    df = df.sort_values('step').reset_index(drop=True)
    
    # Linear interpolation for missing G_t values
    df['G_t_interp'] = df['G_t'].interpolate(method='linear')
    
    # If interpolation still leaves NaNs (e.g., at edges), forward/backward fill or drop
    # For derivative calculation, we need consecutive steps. 
    # Strategy: Drop rows where interpolated G_t is still NaN (missing timesteps that can't be bridged)
    df_clean = df.dropna(subset=['G_t_interp']).reset_index(drop=True)
    
    if len(df_clean) < 2:
        # Not enough data for derivative
        df['dG_t'] = np.nan
        df['z_G_t'] = np.nan
        return df
    
    # 2. Compute discrete derivative dG(t) = G(t) - G(t-1)
    # Use the interpolated values
    df_clean['dG_t'] = df_clean['G_t_interp'].diff()
    
    # 3. Compute rolling z-score
    # Z-score = (x - mean) / std
    # Window: rolling mean and std over 'window' samples
    # Handle zero-variance: if std == 0, z-score = 0
    
    rolling_mean = df_clean['G_t_interp'].rolling(window=window, min_periods=1).mean()
    rolling_std = df_clean['G_t_interp'].rolling(window=window, min_periods=1).std()
    
    # Avoid division by zero: set z-score to 0 where std is 0 or NaN
    def safe_zscore(x, mean, std):
        if pd.isna(std) or std == 0:
            return 0.0
        return (x - mean) / std
    
    df_clean['z_G_t'] = df_clean.apply(
        lambda row: safe_zscore(row['G_t_interp'], row[rolling_mean.name], row[rolling_std.name]),
        axis=1
    )
    
    # Correction: The rolling calculation above is slightly flawed in apply context.
    # Let's do it vectorized properly.
    df_clean['z_G_t'] = (df_clean['G_t_interp'] - rolling_mean) / rolling_std
    
    # Apply zero-variance rule: if rolling_std is 0 (or NaN from single sample), set z to 0
    # pd.isna(rolling_std) handles the min_periods=1 case where std is NaN for single sample
    df_clean.loc[rolling_std == 0, 'z_G_t'] = 0.0
    df_clean.loc[pd.isna(rolling_std), 'z_G_t'] = 0.0
    
    # Merge back to original index if we dropped rows? 
    # The task asks to handle missing timesteps by interpolation/skip.
    # We return the cleaned dataframe with computed columns.
    # If the original had gaps, we filled them. If we dropped rows, we return the processed subset.
    # For aggregation, we usually want the full time series. 
    # Let's re-merge with original if needed, but for this function, returning the processed clean data is standard.
    # However, to preserve the original index for downstream merging, we can assign back to a copy of original.
    
    # Better approach: Work on original index, fill NaNs, compute, then assign.
    df_result = df.copy()
    df_result['G_t_interp'] = df_result['G_t'].interpolate(method='linear')
    
    # Identify valid rows for derivative (no NaN in G_t_interp)
    valid_mask = df_result['G_t_interp'].notna()
    df_result['dG_t'] = np.nan
    df_result['z_G_t'] = np.nan
    
    if valid_mask.sum() > 1:
        valid_df = df_result[valid_mask].copy()
        valid_df = valid_df.sort_values('step')
        
        # Derivative
        valid_df['dG_t'] = valid_df['G_t_interp'].diff()
        
        # Rolling stats on valid data
        # We need to align these back to the original index
        rolling_mean_valid = valid_df['G_t_interp'].rolling(window=window, min_periods=1).mean()
        rolling_std_valid = valid_df['G_t_interp'].rolling(window=window, min_periods=1).std()
        
        # Z-score calculation
        valid_df['z_G_t'] = (valid_df['G_t_interp'] - rolling_mean_valid) / rolling_std_valid
        
        # Zero-variance handling: set to 0 if std is 0 or NaN
        valid_df.loc[rolling_std_valid == 0, 'z_G_t'] = 0.0
        valid_df.loc[pd.isna(rolling_std_valid), 'z_G_t'] = 0.0
        
        # Map back to original dataframe
        df_result.loc[valid_df.index, 'dG_t'] = valid_df['dG_t']
        df_result.loc[valid_df.index, 'z_G_t'] = valid_df['z_G_t']
    
    return df_result

def process_all_trajectories(logs: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Process a list of trajectory DataFrames: compute G(t), dG(t), z-score.
    Concatenates results.
    """
    processed = []
    for df in logs:
        df = compute_divergence_gap(df)
        df = compute_derivative_and_zscore(df)
        processed.append(df)
    
    if not processed:
        return pd.DataFrame()
    
    return pd.concat(processed, ignore_index=True)

def aggregate_seed_logs(log_dir: Path, output_path: Path):
    """
    Main entry point for T016/T017: Load logs, compute metrics, handle edge cases,
    and save to CSV.
    """
    logs = load_trajectory_logs(log_dir)
    if not logs:
        raise ValueError("No valid trajectory logs found.")
    
    combined = process_all_trajectories(logs)
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    # Save
    write_csv(combined, output_path)
    print(f"Saved processed trajectories to {output_path}")
    return combined

def main():
    """
    Entry point for script execution.
    """
    root = get_project_root()
    log_dir = root / "data" / "raw"
    output_path = root / "data" / "processed" / "trajectories_divergence.csv"
    
    if not log_dir.exists():
        # Check if raw data exists, if not, try to find it or error
        print(f"Error: Raw log directory not found at {log_dir}")
        sys.exit(1)
    
    aggregate_seed_logs(log_dir, output_path)

if __name__ == "__main__":
    main()
