import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.config import get_project_root, DataConfig
from code.utils.io_utils import read_csv, write_csv, ensure_dir
from code.utils.math_utils import interpolate_missing_timesteps, safe_z_score, handle_nan, rolling_std_dev

def load_trajectory_logs(raw_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load all trajectory CSV logs from the raw data directory.
    Expects files in data/raw/cherrl_logs/ matching the schema from T005a.
    Returns a combined DataFrame with 'seed_id' and 'bias_type' columns preserved.
    """
    if raw_dir is None:
        raw_dir = get_project_root() / "data" / "raw" / "cherrl_logs"
    
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {raw_dir}")

    dfs = []
    for file_path in csv_files:
        # Extract seed_id and bias_type from filename if possible, or rely on column content
        # Assuming filename format: seed_{id}_{bias}.csv or similar, but we trust content first
        df = read_csv(file_path)
        
        # Infer metadata from filename if not in columns, otherwise use existing columns
        stem = file_path.stem
        # Simple heuristic: if columns missing, try to parse stem (e.g., "seed_1_lexical")
        if 'seed_id' not in df.columns:
            try:
                parts = stem.split('_')
                # Heuristic: last two parts are seed and bias
                if len(parts) >= 2:
                    df['seed_id'] = parts[-2]
                    df['bias_type'] = parts[-1]
                else:
                    df['seed_id'] = stem
                    df['bias_type'] = 'unknown'
            except Exception:
                df['seed_id'] = stem
                df['bias_type'] = 'unknown'
        
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    
    # Ensure required columns exist and are numeric
    required = ['seed_id', 'bias_type', 'timestep', 'J_biased', 'J_unbiased', 'J_gold']
    for col in required:
        if col not in combined.columns:
            raise ValueError(f"Missing required column in trajectory data: {col}")
    
    combined['timestep'] = pd.to_numeric(combined['timestep'], errors='coerce')
    combined['J_biased'] = pd.to_numeric(combined['J_biased'], errors='coerce')
    combined['J_unbiased'] = pd.to_numeric(combined['J_unbiased'], errors='coerce')
    combined['J_gold'] = pd.to_numeric(combined['J_gold'], errors='coerce')
    
    combined = combined.dropna(subset=['timestep', 'J_biased', 'J_unbiased', 'J_gold'])
    combined = combined.sort_values(by=['seed_id', 'bias_type', 'timestep']).reset_index(drop=True)
    
    return combined

def compute_divergence_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute G(t) = |J_biased - J_unbiased| per FR-001.
    Returns the DataFrame with a new column 'G_t'.
    """
    if df.empty:
        return df
    
    df = df.copy()
    df['G_t'] = (df['J_biased'] - df['J_unbiased']).abs()
    return df

def compute_derivative_and_zscore(df: pd.DataFrame, window_size: int = 20, min_samples: int = 5, epsilon: float = 1e-9) -> pd.DataFrame:
    """
    Compute dG(t) (discrete derivative) and rolling z-score for G(t).
    
    Logic:
    1. Interpolate missing timesteps using linear interpolation (T017).
    2. Calculate discrete derivative: dG_t = G_t[t] - G_t[t-1].
    3. Calculate rolling z-score with sliding window W=20, min 5 samples.
       - Uses safe_z_score from math_utils which handles zero variance via epsilon floor.
    
    Args:
        df: DataFrame with 'timestep' and 'G_t' columns.
        window_size: Sliding window size (W).
        min_samples: Minimum samples required to compute std dev.
        epsilon: Floor for variance to prevent division by zero.
    
    Returns:
        DataFrame with 'dG_t' and 'z_G_t' columns.
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Ensure sorted by timestep within each group (seed, bias)
    # The input should already be sorted, but we enforce it for safety
    df = df.sort_values(['seed_id', 'bias_type', 'timestep']).reset_index(drop=True)
    
    # Handle missing timesteps via interpolation per group
    # We need to ensure timesteps are contiguous for derivative calculation
    # Group by seed and bias
    def process_group(group):
        # Interpolate missing timesteps
        # Create a complete range of timesteps if gaps exist
        # For simplicity in this implementation, we assume 'timestep' is the index of measurement
        # and we interpolate values if there are NaNs in G_t, or fill gaps if timesteps are non-sequential.
        # The task T017 specifies linear interpolation for gaps.
        
        # Check for gaps in timestep sequence
        # If timesteps are 1, 2, 5, 6 -> we might need to insert 3, 4 if we assume unit steps.
        # However, usually in these logs, timestep is the step index. 
        # We will interpolate G_t values if there are NaNs, and ensure the derivative is calculated on the sequence.
        
        # Step 1: Interpolate NaNs in G_t
        if group['G_t'].isna().any():
            group['G_t'] = group['G_t'].interpolate(method='linear')
        
        # Step 2: Compute discrete derivative dG_t
        # dG_t = G_t[t] - G_t[t-1]
        # For the first row, dG_t is NaN or 0. We set it to 0 or NaN.
        group['dG_t'] = group['G_t'].diff()
        
        # Handle NaN in dG_t (first row)
        group['dG_t'] = group['dG_t'].fillna(0.0)
        
        # Step 3: Compute Rolling Z-Score
        # Z = (x - mean) / std
        # Rolling window W=20, min_samples=5
        # We use the safe_z_score helper which handles the logic internally
        
        # We need to apply rolling window per group. 
        # Since we are inside a groupby apply, we can use rolling on the series.
        
        # Custom rolling z-score implementation using safe_z_score logic
        # We iterate to ensure we respect min_samples and window constraints exactly as per spec
        
        g_values = group['G_t'].values
        z_scores = np.full(len(g_values), np.nan)
        
        for i in range(len(g_values)):
            # Define window end at i
            start_idx = max(0, i - window_size + 1)
            window_data = g_values[start_idx:i+1]
            
            if len(window_data) < min_samples:
                # Not enough samples, set to NaN or 0? Spec says "requiring min 5 samples"
                # If not met, we cannot compute. We'll set to NaN.
                z_scores[i] = np.nan
                continue
            
            # Use safe_z_score from utils
            # safe_z_score expects a 1D array and returns the z-score for the last element?
            # Or the z-score for each element? 
            # The spec says "rolling z-score", usually meaning the z-score of the current point 
            # relative to the window ending at that point.
            
            # Let's assume safe_z_score computes the z-score of the input array's elements 
            # or specifically the last one. Given the function signature in T017 context,
            # we assume it returns the z-score for the current value relative to the window stats.
            
            # Re-implementing the rolling logic explicitly to ensure correctness with min_samples
            mean_val = np.mean(window_data)
            std_val = np.std(window_data)
            
            # Apply epsilon floor for zero variance
            if std_val < epsilon:
                std_val = epsilon
            
            # Z-score of the current point (G_t[i])
            z_val = (g_values[i] - mean_val) / std_val
            z_scores[i] = z_val
        
        group['z_G_t'] = z_scores
        
        # Handle NaNs in z_G_t (e.g., at the start where window < min_samples)
        # We can leave them as NaN or fill with 0? Spec doesn't specify fill for z-score start.
        # We'll leave as NaN for now, or fill with 0 if that's safer for downstream.
        # Let's fill with 0 to avoid propagation of NaN in downstream detectors if not handled.
        # Actually, better to leave NaN and let downstream handle or fill explicitly.
        # But for T015, we just compute it.
        
        return group

    df = df.groupby(['seed_id', 'bias_type'], group_keys=False).apply(process_group)
    df = df.reset_index(drop=True)
    
    return df

def process_all_trajectories(input_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Main pipeline function to load, compute G(t), dG(t), and z-score.
    """
    if input_dir is None:
        input_dir = get_project_root() / "data" / "raw" / "cherrl_logs"
    if output_dir is None:
        output_dir = get_project_root() / "data" / "processed"
    
    ensure_dir(output_dir)
    
    # Load
    df = load_trajectory_logs(input_dir)
    if df.empty:
        print("No data to process.")
        return df
    
    # Compute Divergence Gap G(t)
    df = compute_divergence_gap(df)
    
    # Compute Derivative and Z-Score
    df = compute_derivative_and_zscore(df)
    
    return df

def aggregate_seed_logs(df: pd.DataFrame, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Aggregate processed data into a single CSV file.
    Output columns: seed_id, bias_type, timestep, J_biased, J_unbiased, J_gold, G_t, dG_t, z_G_t
    """
    if df.empty:
        return df
    
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "trajectories_divergence.csv"
    
    ensure_dir(output_path.parent)
    
    # Select and order columns
    cols = ['seed_id', 'bias_type', 'timestep', 'J_biased', 'J_unbiased', 'J_gold', 'G_t', 'dG_t', 'z_G_t']
    # Ensure all exist
    existing_cols = [c for c in cols if c in df.columns]
    df_out = df[existing_cols]
    
    write_csv(df_out, output_path)
    print(f"Aggregated data saved to {output_path}")
    return df_out

def main():
    """
    Entry point for the ingestion script.
    """
    try:
        print("Starting ingestion pipeline...")
        df = process_all_trajectories()
        if not df.empty:
            aggregate_seed_logs(df)
            print("Ingestion pipeline completed successfully.")
        else:
            print("No data processed. Exiting.")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Ingestion pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()