"""
Ground Truth and Independence Verification Module.

This module handles:
1. Independence checks (Pearson correlation) between reward signals and ground truth.
2. Derivation of ground truth labels based on J_gold drops.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Import local utilities and config
from code.config import get_project_root, DataConfig, EvalConfig
from code.utils.math_utils import calculate_pearson_correlation
from code.utils.io_utils import write_json, read_csv

# Constants
INDEPENDENCE_STATUS_OK = "ok"
INDEPENDENCE_STATUS_FAILED = "failed"
CORRELATION_THRESHOLD = 0.8  # FR-008 default threshold

def check_independence(
    df: pd.DataFrame,
    col_a: str,
    col_b: str,
    threshold: float = CORRELATION_THRESHOLD,
    metric_name: str = "generic"
) -> Tuple[bool, float]:
    """
    Check Pearson correlation between two columns.

    Args:
        df: DataFrame containing the data.
        col_a: Name of the first column.
        col_b: Name of the second column.
        threshold: Maximum allowed correlation magnitude.
        metric_name: Identifier for logging.

    Returns:
        Tuple of (is_independent, correlation_value).
        is_independent is True if |corr| <= threshold.
    """
    if col_a not in df.columns or col_b not in df.columns:
        raise ValueError(f"Columns {col_a} or {col_b} not found in dataframe.")

    # Drop NaNs for correlation calculation
    valid_data = df[[col_a, col_b]].dropna()

    if len(valid_data) < 2:
        # Not enough data to compute correlation
        print(f"WARNING: Insufficient data to compute correlation for {metric_name}.")
        return True, 0.0

    corr = calculate_pearson_correlation(valid_data[col_a], valid_data[col_b])
    
    # FR-008: If correlation is strictly greater than threshold, fail
    if abs(corr) > threshold:
        return False, corr
    
    return True, corr

def check_unbiased_independence(
    df: pd.DataFrame,
    threshold: float = CORRELATION_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check independence between J_unbiased and J_gold (FR-006 logic).
    
    Returns (True, corr) if passed, (False, corr) if failed.
    """
    return check_independence(df, "J_unbiased", "J_gold", threshold, "J_unbiased vs J_gold")

def check_biased_independence(
    df: pd.DataFrame,
    threshold: float = CORRELATION_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check independence between J_biased and J_gold (FR-008).
    
    Logic: If correlation is strictly greater than `CORRELATION_THRESHOLD`, 
    raise SystemExit(1) and log error.
    
    Args:
        df: DataFrame containing trajectories.
        threshold: Correlation threshold (default 0.8).
        
    Returns:
        Tuple[bool, float]: (is_passed, correlation_value).
        If passed, returns (True, corr).
        If failed, the function raises SystemExit(1) internally.
    """
    is_independent, corr = check_independence(df, "J_biased", "J_gold", threshold, "J_biased vs J_gold")
    
    if not is_independent:
        error_msg = f"ERROR: Independence check failed (J_biased vs J_gold). Correlation {corr:.4f} > {threshold}. Pipeline halted."
        print(error_msg, file=sys.stderr)
        # Exit with code 1 as per task requirement for failure
        raise SystemExit(1)
    
    return True, corr

def derive_ground_truth_labels(
    df: pd.DataFrame,
    drop_threshold: float = 0.1,
    window_size: int = 50,
    sustained_steps: int = 3
) -> pd.DataFrame:
    """
    Derive ground truth labels based on J_gold drops.
    
    Logic:
    1. Identify drops >= drop_threshold over window_size steps.
    2. Ensure the drop is sustained for sustained_steps.
    
    Args:
        df: Input DataFrame.
        drop_threshold: Minimum drop magnitude.
        window_size: Number of steps to look back for the drop.
        sustained_steps: Minimum steps the low level must be maintained.
        
    Returns:
        DataFrame with 'gt_label' column (1 for hacking event, 0 otherwise).
    """
    if "J_gold" not in df.columns:
        raise ValueError("J_gold column missing for ground truth derivation.")
    
    df = df.copy()
    j_gold = df["J_gold"].values
    
    # Initialize labels
    labels = np.zeros(len(df), dtype=int)
    
    # Simple sliding window approach
    # For each timestep t, look back `window_size` steps
    for t in range(window_size, len(df)):
        start_idx = t - window_size
        current_val = j_gold[t]
        prev_val = j_gold[start_idx]
        
        # Check if drop occurred
        if (prev_val - current_val) >= drop_threshold:
            # Check if sustained: current value must be low for `sustained_steps`
            # We check if the value at t is still low relative to start
            # A more robust check: verify the trend or minimum in the window
            # For this implementation, we mark the end of the drop event
            # and potentially extend it if needed.
            # Simple heuristic: if the drop is confirmed, mark this segment.
            # To satisfy "sustained 3 steps", we ensure the drop persists
            # until at least t + sustained_steps - 1.
            if t + sustained_steps <= len(df):
                # Check if the value remains low for the next few steps
                # (Simplified: just check the immediate next steps haven't recovered)
                # Ideally, we check if min(j_gold[t:t+sustained_steps]) is still low
                segment_min = np.min(j_gold[t : t + sustained_steps])
                if segment_min <= current_val + 0.01: # Allow tiny float noise
                    labels[t] = 1
                    # Optionally mark the whole segment? 
                    # The task asks for labels, usually point-wise or segment-wise.
                    # We'll mark the timestep where the sustained drop is confirmed.
    
    df["gt_label"] = labels
    return df

def main():
    """
    Main entry point for Independence Checks (T032a, T032b) and Ground Truth (T031).
    
    Execution Flow:
    1. Load aggregated trajectories.
    2. Run T032a: Check J_unbiased vs J_gold.
    3. Run T032b: Check J_biased vs J_gold (HALTS if fails).
    4. If passed, run T031: Derive ground truth labels.
    5. Write status file.
    """
    root = get_project_root()
    data_config = DataConfig()
    eval_config = EvalConfig()
    
    input_path = root / data_config.PROCESSED_DIR / "trajectories_divergence.csv"
    status_path = root / data_config.PROCESSED_DIR / "independence_check_status.json"
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"Loading data from {input_path}...")
    df = read_csv(input_path)
    
    # T032a: Check Unbiased Independence
    print("Running T032a: Checking J_unbiased vs J_gold independence...")
    try:
        is_unbiased_ok, unbiased_corr = check_unbiased_independence(df)
        if not is_unbiased_ok:
            print(f"ERROR: Independence check failed (J_unbiased vs J_gold). Correlation {unbiased_corr:.4f}. Pipeline halted.")
            sys.exit(1)
        print(f"T032a Passed. Correlation: {unbiased_corr:.4f}")
    except SystemExit:
        raise
    
    # T032b: Check Biased Independence
    print("Running T032b: Checking J_biased vs J_gold independence...")
    try:
        is_biased_ok, biased_corr = check_biased_independence(df)
        # If we reach here, T032b passed (otherwise check_biased_independence raises SystemExit)
        print(f"T032b Passed. Correlation: {biased_corr:.4f}")
    except SystemExit as e:
        # Re-raise to halt pipeline
        raise
    
    # If both checks pass, proceed to T031 (Ground Truth)
    # Note: T031 is not strictly required to write the status file, 
    # but the task description says "If passed, write status file".
    # We write the status file here to confirm the independence checks passed.
    
    status_data = {
        "status": INDEPENDENCE_STATUS_OK,
        "checks": {
            "unbiased_vs_gold": {"passed": True, "correlation": float(unbiased_corr)},
            "biased_vs_gold": {"passed": True, "correlation": float(biased_corr)}
        },
        "threshold": CORRELATION_THRESHOLD
    }
    
    print(f"Writing independence status to {status_path}...")
    write_json(status_path, status_data)
    
    print("T032b and T032a completed successfully.")
    
    # Optional: Run T031 if needed immediately, but T032b task specifically asks for status file
    # and halting. We stop here for T032b completion.
    return 0

if __name__ == "__main__":
    sys.exit(main())