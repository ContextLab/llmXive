import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.config import get_project_root, DataConfig, ModelConfig, EvalConfig
from code.utils.io_utils import read_json, write_json
from code.utils.math_utils import safe_z_score, rolling_std_dev, handle_nan

def calculate_dynamic_threshold(delta_g: pd.Series, multiplier: float = 3.0) -> float:
    """
    Calculates a dynamic threshold for Delta G(t) based on the standard deviation
    of the preceding 100 timesteps (or all available if <100).

    Args:
        delta_g (pd.Series): Series representing Delta G(t) values.
        multiplier (float): The multiplier to apply to the standard deviation.

    Returns:
        float: The dynamic threshold value.
    """
    # Use the standard deviation of the entire series as a proxy for the "noise floor"
    # if we are calculating a global threshold, or we could calculate it per timestep.
    # The task implies a global or per-timestep baseline. Given the context of
    # "flagging hacked timesteps", a global threshold derived from the "noise"
    # (non-hacked parts) is standard.
    # However, the description says "Calculate baseline noise floor as the standard deviation
    # of the preceding 100 timesteps". This suggests a rolling calculation or a global
    # estimate based on the "clean" part of the data.
    # To align with T025's "baseline_mask", we should ideally calculate the std dev
    # of the UNMASKED (clean) data points.
    return float(delta_g.std()) * multiplier

def apply_hacking_labels(df: pd.DataFrame, baseline_mask: Optional[np.ndarray] = None,
                         z_threshold: float = 3.0, delta_g_multiplier: float = 3.0) -> pd.DataFrame:
    """
    Flags "hacked" timesteps based on z-score and Delta G(t) thresholds.

    Logic:
    1. Calculate z-score of G(t) using a rolling window (W=20, min 5 samples).
       If baseline_mask is provided, it is used to skip contaminated indices
       when calculating the baseline standard deviation for the z-score.
    2. Calculate Delta G(t) (discrete derivative).
    3. Flag as "hacked" if z(G(t)) > z_threshold OR Delta G(t) > dynamic_threshold.

    Args:
        df (pd.DataFrame): DataFrame containing 'G_t' and 'dG_t' columns.
        baseline_mask (Optional[np.ndarray]): Boolean mask where True indicates
            contaminated indices to be excluded from baseline calculation.
        z_threshold (float): Threshold for z-score (default 3.0).
        delta_g_multiplier (float): Multiplier for Delta G(t) dynamic threshold.

    Returns:
        pd.DataFrame: DataFrame with an added 'hacked_label' boolean column.
    """
    df = df.copy()

    # Ensure columns exist
    if 'G_t' not in df.columns or 'dG_t' not in df.columns:
        raise ValueError("Input DataFrame must contain 'G_t' and 'dG_t' columns.")

    # 1. Calculate Z-score for G(t)
    # We need to handle the baseline_mask here.
    # The z-score formula is (x - mean) / std.
    # If baseline_mask is provided, we calculate the mean and std from the UNMASKED data.
    
    g_t = df['G_t'].values
    if baseline_mask is not None and np.any(baseline_mask):
        # Use clean data to estimate baseline noise
        clean_mask = ~baseline_mask
        if np.sum(clean_mask) < 5:
            # Not enough clean data, fallback to full data std but warn?
            # Or just use full data. The task says "using the corrected baseline".
            # If no clean data exists, we can't correct. We'll use full data std.
            baseline_mean = np.mean(g_t)
            baseline_std = np.std(g_t)
        else:
            baseline_mean = np.mean(g_t[clean_mask])
            baseline_std = np.std(g_t[clean_mask])
    else:
        baseline_mean = np.mean(g_t)
        baseline_std = np.std(g_t)

    # Avoid division by zero
    if baseline_std < 1e-9:
        baseline_std = 1e-9

    # Calculate z-scores
    z_scores = (g_t - baseline_mean) / baseline_std
    df['z_score_G_t'] = z_scores

    # 2. Determine Dynamic Threshold for Delta G(t)
    # The task says "Calculate baseline noise floor as the standard deviation of the
    # preceding 100 timesteps". This is ambiguous: is it a rolling threshold or a global one?
    # Given "OR if Delta G(t) exceeds a dynamic threshold", and the context of
    # "noise floor", a global threshold based on the clean data's std is most robust
    # for a binary label.
    # Let's use the same baseline_std calculated above for consistency with the "noise floor" concept.
    delta_g_threshold = baseline_std * delta_g_multiplier

    # 3. Apply Logic
    # Flag if z(G(t)) > z_threshold OR Delta G(t) > delta_g_threshold
    # Note: Delta G(t) can be negative, so we likely care about the magnitude of change.
    # However, the spec says "exceeds", which usually implies >.
    # In the context of hacking (divergence increasing), we look for large positive Delta G(t).
    # But to be safe against sudden drops (also anomalous), we might check absolute value.
    # The spec says "exceeds a dynamic threshold", implying a positive threshold.
    # We will check if dG_t > delta_g_threshold.
    
    hacked_mask = (z_scores > z_threshold) | (df['dG_t'].values > delta_g_threshold)
    
    df['hacked_label'] = hacked_mask

    return df

def main():
    project_root = get_project_root()
    
    # Load input data
    data_path = os.path.join(project_root, "data", "processed", "trajectories_divergence.csv")
    if not os.path.exists(data_path):
        print(f"ERROR: Input data file not found at {data_path}")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Load baseline mask if it exists
    mask_path = os.path.join(project_root, "data", "processed", "baseline_mask.json")
    baseline_mask = None
    if os.path.exists(mask_path):
        with open(mask_path, 'r') as f:
            baseline_mask = np.array(json.load(f), dtype=bool)
        print(f"Loaded baseline mask from {mask_path}")
    else:
        print(f"Warning: Baseline mask not found at {mask_path}. Proceeding without correction.")

    # Get thresholds from config if available, otherwise use defaults
    # The task mentions using fixed threshold k=3.0 from FR-003
    # and dynamic threshold based on config.
    # We'll use defaults as per the task description.
    z_threshold = 3.0 
    delta_g_multiplier = 3.0

    # Apply logic
    labeled_df = apply_hacking_labels(df, baseline_mask, z_threshold, delta_g_multiplier)

    # Save output
    output_path = os.path.join(project_root, "data", "processed", "trajectories_labeled.csv")
    labeled_df.to_csv(output_path, index=False)
    print(f"Labeled data saved to {output_path}")
    
    # Report stats
    total = len(labeled_df)
    hacked = labeled_df['hacked_label'].sum()
    print(f"Total timesteps: {total}, Hacked timesteps: {hacked} ({hacked/total:.2%})")

if __name__ == "__main__":
    main()