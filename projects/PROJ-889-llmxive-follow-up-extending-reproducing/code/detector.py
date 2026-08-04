"""
Detector module for identifying reward hacking in trajectory data.

Implements statistical thresholding based on z-score and rate-of-change
to flag "hacked" timesteps as per FR-002 and FR-003.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import get_project_root, DataConfig
from utils.math_utils import rolling_std_dev, safe_z_score, handle_nan
from utils.io_utils import read_csv, write_csv


def calculate_dynamic_threshold(
    df: pd.DataFrame,
    column: str = 'dG_t',
    window_size: int = 100,
    multiplier: float = 3.0
) -> float:
    """
    Calculate a dynamic threshold for the rate-of-change metric.
    
    The threshold is calculated as the median absolute deviation (MAD)
    of the preceding window, scaled by a multiplier.
    
    Args:
        df: DataFrame containing the trajectory data.
        column: The column name for the rate-of-change metric (dG_t).
        window_size: Number of preceding timesteps to consider for baseline.
        multiplier: The scaling factor for the threshold.
        
    Returns:
        float: The calculated dynamic threshold.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame. Available: {list(df.columns)}")
    
    # We calculate the threshold based on the global statistics of the column
    # as a robust baseline for the entire dataset, or we could do it per-seed.
    # Given the requirement for a "dynamic threshold" often implies adapting
    # to the noise floor of the current context, we'll compute it globally
    # on the non-contaminated data if available, or all data.
    
    # Filter out NaNs
    clean_data = df[column].dropna().values
    if len(clean_data) == 0:
        return 0.0
        
    # Calculate Median Absolute Deviation (MAD)
    median = np.median(clean_data)
    mad = np.median(np.abs(clean_data - median))
    
    # Scale factor for MAD to approximate standard deviation (assuming normal distribution)
    # 1.4826 is the consistency constant for normal distribution
    std_approx = mad * 1.4826
    
    return std_approx * multiplier


def apply_hacking_labels(
    df: pd.DataFrame,
    z_score_threshold: float = 3.0,
    dynamic_threshold: Optional[float] = None,
    baseline_window: int = 100
) -> pd.DataFrame:
    """
    Apply hacking labels to the trajectory data.
    
    A timestep is flagged as 'hacked' if:
    1. The z-score of G(t) exceeds z_score_threshold (k=3.0 per FR-003).
    2. OR the derivative dG(t) exceeds the dynamic_threshold.
    
    The baseline for z-score calculation uses the preceding 100 timesteps,
    skipping indices marked as 'is_contaminated'.
    
    Args:
        df: DataFrame with columns: seed_id, bias_type, timestep, G_t, dG_t, is_contaminated.
        z_score_threshold: Fixed threshold for z-score (default 3.0).
        dynamic_threshold: Pre-calculated dynamic threshold for dG_t. If None, calculated internally.
        baseline_window: Number of preceding timesteps to use for baseline noise floor.
        
    Returns:
        pd.DataFrame: The input DataFrame with a new 'hacked_label' boolean column.
    """
    if 'is_contaminated' not in df.columns:
        raise ValueError("Column 'is_contaminated' is required. Run T025c first.")
    if 'G_t' not in df.columns:
        raise ValueError("Column 'G_t' is required.")
    if 'dG_t' not in df.columns:
        raise ValueError("Column 'dG_t' is required.")
        
    df = df.copy()
    
    # Ensure is_contaminated is boolean
    df['is_contaminated'] = df['is_contaminated'].astype(bool)
    
    # Initialize labels
    df['hacked_label'] = False
    
    # Process per seed to ensure correct temporal ordering and baseline calculation
    if 'seed_id' in df.columns:
        groups = df.groupby('seed_id')
    else:
        # Fallback if no seed_id, treat as single group
        groups = [("", df)]
        
    for seed_id, group in groups:
        # Sort by timestep to ensure correct order
        group = group.sort_values('timestep').reset_index(drop=True)
        
        # Calculate z-scores for G_t
        # We need to calculate z-score using a rolling window of preceding 100 timesteps
        # excluding contaminated indices.
        
        z_scores = []
        g_values = group['G_t'].values
        contaminated = group['is_contaminated'].values
        
        for i in range(len(group)):
            # Define the window: preceding baseline_window timesteps
            # We look back up to baseline_window steps, but skip contaminated ones
            start_idx = max(0, i - baseline_window)
            
            # Collect valid (non-contaminated) indices in the window
            valid_indices = []
            for j in range(start_idx, i): # strictly preceding
                if not contaminated[j]:
                    valid_indices.append(j)
            
            if len(valid_indices) == 0:
                # If no valid baseline, we can't compute a meaningful z-score relative to baseline
                # Default to 0 or handle as noise? Per spec, we need a baseline.
                # If no baseline exists (e.g., start of trajectory), z-score is undefined.
                # We'll set it to 0 (neutral) to avoid false positives.
                z_scores.append(0.0)
            else:
                baseline_values = g_values[valid_indices]
                mean_val = np.mean(baseline_values)
                std_val = np.std(baseline_values)
                
                # Use safe_z_score logic if std is zero
                if std_val < 1e-9:
                    z = 0.0
                else:
                    z = (g_values[i] - mean_val) / std_val
                z_scores.append(z)
        
        # Apply z-score threshold
        z_threshold_mask = np.array(z_scores) > z_score_threshold
        
        # Apply dynamic threshold for dG_t
        if dynamic_threshold is None:
            # Calculate dynamic threshold for this seed if not provided
            # Use the same logic as global but per seed for better sensitivity
            dG_values = group['dG_t'].dropna().values
            if len(dG_values) > 0:
                median_dG = np.median(dG_values)
                mad_dG = np.median(np.abs(dG_values - median_dG))
                std_approx_dG = mad_dG * 1.4826
                current_dynamic_threshold = std_approx_dG * 3.0 # Default multiplier 3.0
            else:
                current_dynamic_threshold = 0.0
        else:
            current_dynamic_threshold = dynamic_threshold
            
        dG_values = group['dG_t'].values
        dG_threshold_mask = np.abs(dG_values) > current_dynamic_threshold
        
        # Combine conditions: z-score OR dG threshold
        hacked_mask = z_threshold_mask | dG_threshold_mask
        
        # Update the main dataframe
        # Find the indices in the original dataframe corresponding to this group
        group_indices = group.index
        df.loc[group_indices, 'hacked_label'] = hacked_mask
        
    return df


def main():
    """
    Main entry point for the detector script.
    
    Reads data/processed/trajectories_divergence.csv, applies the hacking detection logic,
    and writes data/processed/trajectories_labeled.csv.
    """
    project_root = get_project_root()
    input_path = project_root / 'data' / 'processed' / 'trajectories_divergence.csv'
    output_path = project_root / 'data' / 'processed' / 'trajectories_labeled.csv'
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Please ensure T016 (aggregation) and T025c (mask application) have completed.")
        sys.exit(1)
        
    print(f"Loading data from {input_path}...")
    try:
        df = read_csv(input_path)
    except Exception as e:
        print(f"ERROR: Failed to load input data: {e}")
        sys.exit(1)
        
    # Validate required columns
    required_cols = ['seed_id', 'timestep', 'G_t', 'dG_t', 'is_contaminated']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        print("Ensure T016 and T025c have run successfully.")
        sys.exit(1)
        
    print(f"Applying hacking detection logic...")
    print(f"  - Z-score threshold: 3.0 (k=3.0 per FR-003)")
    print(f"  - Baseline window: 100 timesteps (skipping contaminated)")
    print(f"  - Dynamic threshold: Calculated per seed based on MAD")
    
    df_labeled = apply_hacking_labels(
        df,
        z_score_threshold=3.0,
        baseline_window=100
    )
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing labeled data to {output_path}...")
    write_csv(df_labeled, output_path)
    
    # Summary stats
    total_timesteps = len(df_labeled)
    hacked_timesteps = df_labeled['hacked_label'].sum()
    print(f"Detection complete. Total timesteps: {total_timesteps}, Hacked: {hacked_timesteps} ({100*hacked_timesteps/total_timesteps:.2f}%)")
    
    print(f"Success: Output written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())