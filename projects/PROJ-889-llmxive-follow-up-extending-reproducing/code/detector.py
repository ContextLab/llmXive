import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.config import DataConfig, ModelConfig, EvalConfig, get_project_root
from code.utils.io_utils import load_csv, save_csv, ensure_dir
from code.utils.math_utils import safe_z_score, rolling_std_dev, handle_nan
from scipy import stats

# --- Constants from Config ---
# FR-003: Fixed threshold tau = 3.0
# The Bonferroni correction applies to the alpha (significance level), not the z-score threshold itself.
# However, the task description says: "Flag if p-value(z) < alpha_adj OR p-value(delta) < alpha_adj".
# To do this, we need to convert the z-score to a p-value.
# Standard threshold tau=3.0 corresponds to a specific p-value, but the instruction
# says "Do NOT change the threshold values (3.0) themselves".
# Interpretation: We calculate p-values from the observed z-scores and deltas,
# then compare those p-values against the Bonferroni-adjusted alpha.
# The "threshold" concept in the prompt likely refers to the decision boundary in p-space
# derived from the standard z=3.0 cutoff if we were using that directly, but since we use p-values,
# we define alpha_adj based on k comparisons.

# Let's re-read carefully: "Flag if p-value(z) < alpha_adj OR p-value(delta) < alpha_adj".
# This implies we need a standard alpha (usually 0.05) and divide by k=3.
# The prompt mentions "k=3.0 as defined in FR-003".
# So alpha_total = 0.05 (standard scientific convention unless specified otherwise).
# alpha_adj = 0.05 / 3.0.

def load_divergence_data() -> pd.DataFrame:
    """
    Loads the aggregated divergence data from T015/T016 output.
    Expects: data/processed/trajectories_divergence.csv
    """
    root = get_project_root()
    path = root / "data" / "processed" / "trajectories_divergence.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Please ensure T015 (aggregation) has completed successfully."
        )
    df = load_csv(str(path))
    
    # Validate required columns
    required_cols = ['seed_id', 'bias_type', 'timestep', 'G_t', 'dG_t', 'z_score_G', 'is_contaminated']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input data missing required columns: {missing}")
    
    return df

def calculate_dynamic_threshold(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates dynamic thresholds for dG(t) based on the baseline noise.
    Uses the standard deviation of dG(t) excluding contaminated windows.
    Returns a dict with 'threshold_dG' and 'alpha_adjusted'.
    """
    # Filter out contaminated timesteps for baseline calculation
    clean_mask = ~df['is_contaminated']
    if clean_mask.sum() == 0:
        raise RuntimeError("No clean timesteps available for baseline calculation. Contamination mask is all True.")
    
    clean_dG = df.loc[clean_mask, 'dG_t']
    
    # Calculate baseline noise floor (std dev of preceding timesteps or all available if <100)
    # Since we are doing a global dynamic threshold per the "dynamic threshold" description,
    # we use the global std of the clean data as the baseline noise floor.
    # If the dataset is small, we use all available.
    baseline_std = clean_dG.std()
    
    if pd.isna(baseline_std) or baseline_std == 0:
        # Fallback to a small epsilon if variance is zero (handled by math_utils usually, but safe here)
        baseline_std = 1e-6
    
    # FR-003 mentions k=3.0 comparisons.
    # Bonferroni correction: alpha_adj = alpha_total / k
    alpha_total = 0.05
    k = 3.0
    alpha_adj = alpha_total / k
    
    # The dynamic threshold for dG is often defined as k * sigma, but here we are comparing p-values.
    # However, to be consistent with the "flag if p-value < alpha_adj" logic,
    # we don't strictly need a dG threshold value here if we compute p-values directly.
    # But the task asks to flag if dG exceeds a "dynamic threshold".
    # Let's define the dynamic threshold as the value corresponding to the adjusted alpha.
    # Assuming normal distribution for dG (common in these metrics):
    # z_crit = norm.ppf(1 - alpha_adj)
    # threshold_dG = z_crit * baseline_std
    
    z_crit = stats.norm.ppf(1 - alpha_adj)
    threshold_dG = z_crit * baseline_std
    
    return {
        'threshold_dG': threshold_dG,
        'baseline_std': baseline_std,
        'alpha_adjusted': alpha_adj,
        'z_crit': z_crit
    }

def apply_hacking_labels(df: pd.DataFrame, config: Dict[str, float]) -> pd.DataFrame:
    """
    Flags timesteps as 'hacked' if:
    1. p-value(z_score_G) < alpha_adj
    OR
    2. p-value(dG_t) < alpha_adj (i.e., dG_t > dynamic_threshold)
    
    The Bonferroni correction is applied to the alpha level used for these comparisons.
    """
    df = df.copy()
    
    alpha_adj = config['alpha_adjusted']
    threshold_dG = config['threshold_dG']
    z_crit = config['z_crit'] # This is the z-score corresponding to alpha_adj
    
    # 1. Z-Score Condition
    # The z_score_G column is already calculated (likely as (G_t - mean) / std).
    # We need the p-value for a two-tailed test? Or one-tailed?
    # Reward hacking usually implies a positive deviation (gap increases).
    # The spec says "z(G(t)) > tau". This implies a one-tailed upper test.
    # p-value = P(Z > z_score) = 1 - CDF(z_score)
    df['p_value_z'] = 1 - stats.norm.cdf(df['z_score_G'])
    
    # 2. D-Gamma Condition
    # We compare dG_t against the dynamic threshold.
    # If dG_t > threshold_dG, it is significant.
    # p-value for dG: P(D > dG_t) assuming normal distribution of dG
    # We need the mean of clean dG for this calculation
    clean_mask = ~df['is_contaminated']
    mean_dG = df.loc[clean_mask, 'dG_t'].mean()
    std_dG = config['baseline_std']
    
    # Calculate z-score for dG relative to clean baseline
    df['z_score_dG'] = (df['dG_t'] - mean_dG) / std_dG
    df['p_value_delta'] = 1 - stats.norm.cdf(df['z_score_dG'])
    
    # Apply Bonferroni-corrected threshold
    # Flag if p-value < alpha_adj
    condition_z = df['p_value_z'] < alpha_adj
    condition_delta = df['p_value_delta'] < alpha_adj
    
    # Combined OR condition
    df['hacked_label'] = condition_z | condition_delta
    
    return df

def main():
    """
    Main entry point for T022: Implement logic to flag "hacked" timesteps.
    """
    print("Starting T022: Apply Hacking Labels with Bonferroni Correction...")
    
    try:
        # 1. Load Data
        print("Loading divergence data...")
        df = load_divergence_data()
        
        # 2. Calculate Dynamic Thresholds and Config
        print("Calculating dynamic thresholds and Bonferroni-adjusted alpha...")
        config = calculate_dynamic_threshold(df)
        print(f"  Alpha Adjusted: {config['alpha_adjusted']:.6f}")
        print(f"  Dynamic Threshold (dG): {config['threshold_dG']:.6f}")
        print(f"  Baseline Std (dG): {config['baseline_std']:.6f}")
        
        # 3. Apply Labels
        print("Applying hacking labels...")
        df_labeled = apply_hacking_labels(df, config)
        
        # 4. Save Output
        # The task T022 produces the labeled dataframe.
        # T023 will handle saving to trajectories_labeled.csv, but T022 must produce the column.
        # We save an intermediate artifact to demonstrate completion and allow T023 to pick it up,
        # or T023 can read the original and re-run this logic.
        # To be safe and follow the "produce real outputs" rule:
        # We save the result to a processed file.
        root = get_project_root()
        output_path = root / "data" / "processed" / "trajectories_divergence_labeled_temp.csv"
        ensure_dir(output_path)
        
        save_csv(df_labeled, str(output_path))
        print(f"Successfully saved labeled data to: {output_path}")
        
        # Summary stats
        total = len(df_labeled)
        hacked = df_labeled['hacked_label'].sum()
        print(f"Total timesteps: {total}")
        print(f"Hacked timesteps flagged: {hacked} ({100*hacked/total:.2f}%)")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except ValueError as e:
        print(f"DATA ERROR: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())