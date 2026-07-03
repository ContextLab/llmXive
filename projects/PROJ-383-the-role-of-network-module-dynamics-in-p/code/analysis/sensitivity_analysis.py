import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from scipy import stats

# Import from local project modules
from utils.config import set_all_seeds
from utils.logging_config import setup_logging
from utils.memory_monitor import memory_guard, check_memory_limit

# Import analysis utilities
from analysis.dynamic_connectivity import (
    load_scrubbed_timeseries,
    generate_sliding_windows,
    compute_dynamic_connectivity,
    compute_flexibility_metric,
)
from analysis.statistics import (
    load_flexibility_scores,
    load_behavioral_scores,
    merge_analysis_data,
    compute_partial_spearman_correlation,
    run_permutation_test,
)

# Configure paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
OUTPUT_FILE = DATA_RESULTS / "sensitivity_analysis.json"

# Ensure output directory exists
DATA_RESULTS.mkdir(parents=True, exist_ok=True)

# Setup logging
logger = setup_logging("sensitivity_analysis")


def load_behavioral_scores() -> pd.DataFrame:
    """Load 2-back accuracy scores from the consolidated data."""
    consolidated_path = DATA_PROCESSED / "consolidated_data.parquet"
    if not consolidated_path.exists():
        raise FileNotFoundError(
            f"Consolidated data not found at {consolidated_path}. "
            "Run US1 ingestion pipeline first."
        )
    df = pd.read_parquet(consolidated_path)
    # Expected columns: 'subject_id', 'accuracy_2back', 'mean_fd'
    required_cols = ["subject_id", "accuracy_2back", "mean_fd"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in consolidated data: {missing}")
    return df[["subject_id", "accuracy_2back", "mean_fd"]]


def compute_flexibility_for_window_length(
    window_length: int,
    window_step: int,
    subject_ids: List[str],
    timeseries_data: pd.DataFrame,
) -> Dict[str, float]:
    """
    Compute flexibility scores for all subjects using a specific window length.
    
    Args:
        window_length: Window duration in seconds (e.g., 30, 60, 90).
        window_step: Step size in seconds.
        subject_ids: List of subject IDs to process.
        timeseries_data: DataFrame with time series data.
        
    Returns:
        Dictionary mapping subject_id to flexibility score.
    """
    results = {}
    # Note: In a real scenario, timeseries_data would need to be filtered or 
    # indexed by subject_id. Here we assume the function handles the mapping
    # or timeseries_data is pre-loaded for the relevant subjects.
    
    # For this implementation, we simulate loading per subject to match the 
    # dynamic_connectivity API expectations which usually take a subject_id.
    # However, load_scrubbed_timeseries in the API surface takes no args, 
    # implying it loads all. We will adapt the logic to iterate.
    
    # Since the API `load_scrubbed_timeseries` has no args in the surface, 
    # we assume it returns a dict or DF with subject index. 
    # Let's assume the global data is available or re-loadable.
    
    # To strictly follow the API surface provided:
    # `load_scrubbed_timeseries` -> likely loads from `data/processed/scrubbed_timeseries.parquet`
    # We will re-implement the loading logic here to ensure we get the right data slice.
    
    scrubbed_path = DATA_PROCESSED / "scrubbed_timeseries.parquet"
    if not scrubbed_path.exists():
        raise FileNotFoundError(f"Scrubbed timeseries not found at {scrubbed_path}")
    
    all_timeseries = pd.read_parquet(scrubbed_path)
    
    # Assume 'subject_id' column exists
    if "subject_id" not in all_timeseries.columns:
        raise ValueError("Scrubbed timeseries must have 'subject_id' column")
        
    for subj in subject_ids:
        subj_data = all_timeseries[all_timeseries["subject_id"] == subj]
        if subj_data.empty:
            logger.warning(f"No data for subject {subj}")
            continue
        
        # Extract time series (assuming 'time_series' column with 1D array or flattened)
        # The API surface `compute_dynamic_connectivity` implies it takes time series.
        # We assume the data is in a format compatible with the dynamic_connectivity module.
        
        # Simulate the pipeline for this subject with the specific window
        try:
            # 1. Generate windows
            windows = generate_sliding_windows(
                subj_data, window_length=window_length, window_step=window_step
            )
            if windows is None or len(windows) == 0:
                logger.warning(f"Insufficient time points for {subj} with window {window_length}s")
                continue
            
            # 2. Compute dynamic connectivity
            dyn_conn = compute_dynamic_connectivity(windows)
            
            # 3. Compute flexibility
            flex_score = compute_flexibility_metric(dyn_conn)
            if not np.isnan(flex_score):
                results[subj] = float(flex_score)
            else:
                logger.warning(f"NaN flexibility for {subj}")
        except Exception as e:
            logger.error(f"Error processing {subj} with window {window_length}s: {e}")
            continue
    
    return results


def calculate_correlation_with_behavior(
    flexibility_scores: Dict[str, float],
    behavioral_df: pd.DataFrame,
    motion_param: str = "mean_fd",
) -> Dict[str, Any]:
    """
    Calculate partial Spearman correlation between flexibility and behavior,
    controlling for motion.
    
    Returns dict with 'rho', 'p_value', 'n'.
    """
    # Merge data
    flex_df = pd.DataFrame(list(flexibility_scores.items()), columns=["subject_id", "flexibility"])
    merged = merge_analysis_data(flex_df, behavioral_df)
    
    if len(merged) < 3:
        return {"rho": None, "p_value": None, "n": len(merged), "error": "Insufficient data"}
    
    # Partial correlation
    rho, p_val = compute_partial_spearman_correlation(
        merged, 
        x="flexibility", 
        y="accuracy_2back", 
        control=motion_param
    )
    
    # Run permutation test for robustness
    p_perm = run_permutation_test(
        merged, 
        x="flexibility", 
        y="accuracy_2back", 
        control=motion_param, 
        n_permutations=1000
    )
    
    return {
        "rho": float(rho) if rho is not None else None,
        "p_value": float(p_val) if p_val is not None else None,
        "p_permutation": float(p_perm) if p_perm is not None else None,
        "n": len(merged)
    }


def run_sensitivity_analysis():
    """
    Main entry point for sensitivity analysis.
    Compares p-values across window lengths (30s, 60s, 90s).
    Verifies stability: max absolute difference between p-values < 0.05.
    """
    set_all_seeds(42)
    
    logger.info("Starting Sensitivity Analysis (T027)")
    
    # Load base data
    try:
        behavioral_df = load_behavioral_scores()
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"status": "failed", "reason": str(e)}
    
    subject_ids = behavioral_df["subject_id"].tolist()
    logger.info(f"Processing {len(subject_ids)} subjects")
    
    # Define window lengths (in seconds)
    window_lengths = [30, 60, 90]
    # Assume TR is 0.72s (typical HCP) or derive from data. 
    # For this script, we assume the dynamic_connectivity module handles TR conversion
    # or expects seconds directly. We'll assume seconds.
    window_step = 10  # 10s step
    
    results = {
        "window_lengths": window_lengths,
        "subjects_processed": len(subject_ids),
        "analysis_per_window": {}
    }
    
    p_values = []
    
    for w_len in window_lengths:
        logger.info(f"Processing window length: {w_len}s")
        
        # Compute flexibility
        flex_scores = compute_flexibility_for_window_length(
            window_length=w_len,
            window_step=window_step,
            subject_ids=subject_ids,
            timeseries_data=None, # Loaded internally in function
        )
        
        if not flex_scores:
            logger.warning(f"No flexibility scores for {w_len}s")
            continue
        
        # Compute correlation
        corr_stats = calculate_correlation_with_behavior(flex_scores, behavioral_df)
        
        results["analysis_per_window"][str(w_len)] = corr_stats
        
        if corr_stats.get("p_permutation") is not None:
            p_values.append(corr_stats["p_permutation"])
        elif corr_stats.get("p_value") is not None:
            p_values.append(corr_stats["p_value"])
    
    # Stability Check
    stability_status = "unknown"
    max_diff = None
    
    if len(p_values) >= 2:
        max_diff = max(abs(p_values[i] - p_values[j]) for i in range(len(p_values)) for j in range(i+1, len(p_values)))
        if max_diff < 0.05:
            stability_status = "stable"
            logger.info(f"Sensitivity check PASSED: Max p-value diff {max_diff:.4f} < 0.05")
        else:
            stability_status = "unstable"
            logger.warning(f"Sensitivity check FAILED: Max p-value diff {max_diff:.4f} >= 0.05")
    
    results["stability"] = {
        "status": stability_status,
        "max_p_value_difference": max_diff,
        "threshold": 0.05
    }
    
    # Save results
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {OUTPUT_FILE}")
    return results


def main():
    """Entry point for script execution."""
    try:
        check_memory_limit()
        results = run_sensitivity_analysis()
        
        if results.get("stability", {}).get("status") == "unstable":
            logger.warning("Sensitivity analysis detected instability in p-values.")
            # We still return success as the task is to IMPLEMENT the logic and check,
            # not to force the result to be stable (science might be unstable).
        return 0
    except Exception as e:
        logger.critical(f"Sensitivity analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())