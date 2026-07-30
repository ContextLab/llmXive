import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd

from config import get_project_root
from utils.io_utils import read_csv, write_csv, ensure_dir
from utils.math_utils import rolling_std_dev

def calculate_contaminated_mask(df: pd.DataFrame, threshold_multiplier: float = 3.0) -> pd.Series:
    """
    Identify contiguous segments where G(t) > threshold_multiplier * global_median(G).
    
    Args:
        df: DataFrame containing the 'G_t' column.
        threshold_multiplier: Multiplier for the global median (default 3.0 per FR-009).
        
    Returns:
        A boolean Series aligned with the input DataFrame index, where True indicates
        a contaminated timestep (to be excluded from baseline calculations).
    """
    if 'G_t' not in df.columns:
        raise ValueError("Input DataFrame must contain 'G_t' column.")
    
    g_t = df['G_t'].values
    global_median = np.median(g_t)
    
    # Identify raw contaminated indices
    contamination_threshold = threshold_multiplier * global_median
    is_contaminated = g_t > contamination_threshold
    
    # Convert to boolean Series aligned with index
    mask = pd.Series(is_contaminated, index=df.index)
    
    # Ensure contiguous segments are handled (optional refinement if needed, 
    # but strict element-wise > threshold is the primary definition in FR-009 logic)
    # The prompt says "Identify contiguous segments where G(t) > ...", 
    # implying we mask the points that satisfy the condition. 
    # If the condition is met, it's part of a contaminated segment.
    return mask

def generate_baseline_mask(df: pd.DataFrame, contamination_mask: pd.Series) -> pd.Series:
    """
    Generate the final baseline_mask to be used by T022.
    
    This function currently acts as a pass-through or aggregator if multiple 
    contamination sources existed. For T025, it returns the mask generated 
    by calculate_contaminated_mask.
    
    Args:
        df: The input DataFrame (unused here but kept for signature consistency).
        contamination_mask: The boolean series from calculate_contaminated_mask.
        
    Returns:
        The boolean mask where True means the index should be EXCLUDED from baseline stats.
    """
    return contamination_mask

def calculate_dynamic_baseline_stats(
    df: pd.DataFrame, 
    mask: pd.Series,
    window_size: int = 100
) -> Dict[str, Any]:
    """
    Calculate baseline statistics (mean, std) for the preceding window, 
    EXCLUDING contaminated indices marked in the mask.
    
    This is a helper to demonstrate the consumption of the mask, though T022
    will likely integrate this logic directly.
    
    Args:
        df: DataFrame with 'G_t'.
        mask: Boolean series where True = contaminated (exclude).
        window_size: Number of preceding timesteps to consider.
        
    Returns:
        Dict with 'baseline_mean' and 'baseline_std' for valid windows.
    """
    g_t = df['G_t'].values
    valid_indices = ~mask.values
    stats = []
    
    for i in range(len(g_t)):
        start_idx = max(0, i - window_size)
        window_indices = range(start_idx, i)
        
        # Filter window indices by valid (non-contaminated) status
        valid_window_vals = []
        for j in window_indices:
            if valid_indices[j]:
                valid_window_vals.append(g_t[j])
        
        if len(valid_window_vals) > 0:
            stats.append({
                'timestep': i,
                'baseline_mean': np.mean(valid_window_vals),
                'baseline_std': np.std(valid_window_vals) if len(valid_window_vals) > 1 else 0.0
            })
        else:
            stats.append({
                'timestep': i,
                'baseline_mean': np.nan,
                'baseline_std': np.nan
            })
            
    return pd.DataFrame(stats)

def detect_hacking(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    """
    Detect hacking flags using the contaminated mask.
    
    This function demonstrates the consumption of the mask for T022 logic:
    Flag if z(G(t)) > 3.0 OR dG(t) exceeds dynamic threshold, 
    where the baseline for z-score is calculated excluding 'mask' indices.
    
    Args:
        df: DataFrame with 'G_t', 'dG_t'.
        mask: Boolean series of contaminated indices.
        
    Returns:
        DataFrame with 'hacked_label' column.
    """
    # Placeholder for full T022 logic which depends on this mask
    # Implementation of full T022 is outside T025 scope, but we show integration
    df = df.copy()
    df['baseline_mask'] = mask.values
    # In a real T022 run, we would calculate z-scores excluding these indices
    # and set hacked_label based on thresholds.
    return df

def main():
    """
    Main entry point for T025: Contaminated Window Exclusion.
    
    1. Load aggregated trajectories from data/processed/trajectories_divergence.csv.
    2. Calculate contamination mask based on G(t) > 3 * global_median.
    3. Save the baseline_mask to data/processed/baseline_mask.csv.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = project_root / "data" / "processed" / "baseline_mask.csv"
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"Loading data from {input_path}...")
    df = read_csv(input_path)
    
    print("Calculating contaminated mask (G(t) > 3 * global_median)...")
    contaminated_mask = calculate_contaminated_mask(df, threshold_multiplier=3.0)
    
    # Generate the final baseline mask
    baseline_mask = generate_baseline_mask(df, contaminated_mask)
    
    # Create an output DataFrame with the mask
    mask_df = pd.DataFrame({
        'seed_id': df['seed_id'],
        'bias_type': df['bias_type'],
        'timestep': df['timestep'],
        'is_contaminated': baseline_mask.values
    })
    
    ensure_dir(output_path.parent)
    write_csv(mask_df, output_path)
    
    print(f"Baseline mask saved to {output_path}")
    print(f"Total contaminated timesteps: {contaminated_mask.sum()}")
    print(f"Total timesteps: {len(contaminated_mask)}")

if __name__ == "__main__":
    main()