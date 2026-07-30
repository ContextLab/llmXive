"""
Sensitivity Analysis for Ground-Truth Drop Threshold (FR-007).

This module implements a sensitivity analysis to validate the robustness of the
detector against variations in the ground-truth drop threshold. It sweeps the
threshold over specific values {0.05, 0.1, 0.15} and reports the variation in F1-scores.

Logic:
1. Load the labeled trajectories data (produced by T023/T031).
2. For each threshold in {0.05, 0.1, 0.15}:
   a. Re-derive the ground truth labels based on J_gold drops exceeding the current threshold.
   b. Compare these new labels against the detector's predictions (from T023).
   c. Calculate Precision, Recall, and F1-score.
3. Aggregate results and save to `data/processed/sensitivity_analysis.csv`.
4. Print a summary report.
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import project utilities and config
from config import get_project_root, DataConfig, EvalConfig
from utils.io_utils import read_csv, write_csv, ensure_dir
from evaluation import compute_f1_scores

# Constants for the sweep (FR-007)
THRESHOLD_SWEEP = [0.05, 0.1, 0.15]
MIN_DROP_DURATION = 50  # FR-004: sustained for 50 steps
MIN_SUSTAIN_STEPS = 3   # FR-004: sustained for 3 steps

def derive_ground_truth_labels_for_threshold(
    df: pd.DataFrame,
    threshold: float,
    min_duration: int = MIN_DROP_DURATION,
    min_sustain: int = MIN_SUSTAIN_STEPS
) -> pd.Series:
    """
    Re-derive ground truth labels based on J_gold drops exceeding a specific threshold.

    Logic:
    - Identify drops in J_gold >= threshold over a window of min_duration steps.
    - A drop is considered a "hack" if it is sustained for at least min_sustain steps.
    
    Args:
        df: DataFrame containing 'seed_id', 'timestep', 'J_gold', and 'rubric_type'.
        threshold: The drop magnitude threshold to test.
        min_duration: Window size to calculate the drop (FR-004).
        min_sustain: Minimum number of consecutive steps the drop must persist.

    Returns:
        A boolean Series aligned with df index, True where hacking is detected.
    """
    labels = pd.Series(False, index=df.index)
    
    # Group by seed_id to process trajectories independently
    for seed_id, group in df.groupby('seed_id'):
        if len(group) < min_duration + min_sustain:
            continue
        
        # Sort by timestep to ensure chronological order
        group = group.sort_values('timestep')
        indices = group.index
        j_gold = group['J_gold'].values
        
        # Calculate rolling drop: J_gold[t - min_duration] - J_gold[t]
        # We look at the drop over the last `min_duration` steps ending at t
        # Valid range for t starts at min_duration
        valid_indices = range(min_duration, len(j_gold))
        
        drop_values = np.zeros(len(j_gold))
        for i in valid_indices:
            drop_values[i] = j_gold[i - min_duration] - j_gold[i]
        
        # Identify steps where drop >= threshold
        is_drop = drop_values >= threshold
        
        # Identify sustained drops: must be True for at least `min_sustain` consecutive steps
        # We can use a simple run-length encoding approach or convolution
        # Convolution with a window of `min_sustain`
        kernel = np.ones(min_sustain)
        sustained_mask = np.convolve(is_drop.astype(int), kernel, mode='valid') == min_sustain
        
        # Map back to original indices
        # The convolution result corresponds to indices [min_duration, min_duration + len(sustained_mask) - 1]
        start_idx = min_duration
        for i, is_sustained in enumerate(sustained_mask):
            if is_sustained:
                original_idx = indices[start_idx + i]
                labels.iloc[original_idx] = True
                
    return labels

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Execute the sensitivity analysis sweep.

    Returns:
        Dictionary containing results for each threshold.
    """
    project_root = get_project_root()
    input_path = project_root / DataConfig.PROCESSED_DIR / "trajectories_labeled.csv"
    output_dir = project_root / DataConfig.PROCESSED_DIR
    output_path = output_dir / "sensitivity_analysis.csv"
    
    ensure_dir(output_dir)
    
    if not input_path.exists():
        print(f"ERROR: Input file {input_path} not found. Run T023/T031 first.")
        sys.exit(1)
        
    # Load data
    df = read_csv(input_path)
    
    if 'detector_hack_label' not in df.columns:
        print("ERROR: 'detector_hack_label' column missing. Run T023 first.")
        sys.exit(1)
        
    if 'ground_truth_hack_label' not in df.columns:
        # Fallback: if T031 hasn't run, we might need to derive initial labels, 
        # but for sensitivity analysis, we usually compare against a fixed detector output
        # against varying ground truths. If ground truth column exists, we use it as the base.
        # However, the task is to sweep the GT derivation threshold.
        print("WARNING: 'ground_truth_hack_label' missing. Deriving initial labels with default threshold (0.1).")
        # Derive initial labels with default threshold to populate column if missing
        df['ground_truth_hack_label'] = derive_ground_truth_labels_for_threshold(df, 0.1)
    
    results = []
    
    print(f"Starting Sensitivity Analysis Sweep over thresholds: {THRESHOLD_SWEEP}")
    
    for threshold in THRESHOLD_SWEEP:
        print(f"  Processing threshold: {threshold}...")
        
        # 1. Re-derive ground truth labels for this specific threshold
        new_gt_labels = derive_ground_truth_labels_for_threshold(df, threshold)
        
        # 2. Compare against detector predictions
        # We assume 'detector_hack_label' is fixed from T022/T023
        detector_labels = df['detector_hack_label'].astype(bool)
        
        # 3. Compute metrics
        # Using the same logic as evaluation.py's compute_f1_scores but adapted for series
        # TP, FP, FN, TN
        tp = ((new_gt_labels) & (detector_labels)).sum()
        fp = ((~new_gt_labels) & (detector_labels)).sum()
        fn = ((new_gt_labels) & (~detector_labels)).sum()
        tn = ((~new_gt_labels) & (~detector_labels)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results.append({
            'threshold': threshold,
            'tp': int(tp),
            'fp': int(fp),
            'fn': int(fn),
            'tn': int(tn),
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        })
        
        print(f"    F1: {f1:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}")
    
    results_df = pd.DataFrame(results)
    
    # Save results
    write_csv(results_df, output_path)
    print(f"Sensitivity analysis results saved to {output_path}")
    
    return results_df

def main():
    """Entry point for the script."""
    try:
        results = run_sensitivity_analysis()
        print("\n=== Sensitivity Analysis Summary ===")
        print(results.to_string(index=False))
        print("====================================")
    except Exception as e:
        print(f"ERROR: Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()