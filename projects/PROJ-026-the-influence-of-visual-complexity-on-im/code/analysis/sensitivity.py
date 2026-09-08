"""
Sensitivity Analysis: Threshold Sweep.

This module implements the threshold sweep analysis for visual complexity.
It reads the complexity scores, calculates the standard deviation of the
chosen metric (edge_density), and re-runs the permutation test logic
on subsets of data defined by shifting the complexity threshold.

Logic:
1. Read data/processed/complexity_scores.csv (from T017c).
2. Calculate SD of the 'edge_density' metric.
3. Define shifts: [-0.15, -0.10, -0.05, 0.05, 0.10, 0.15] * SD.
4. For each shift:
   - Adjust the median threshold used for categorization.
   - Re-categorize the stimuli.
   - Join with D-scores (T026b).
   - Filter for valid paired data.
   - If n < 15 per condition, mark as 'invalid'.
   - Otherwise, run the permutation test logic (mean diff, p-value).
5. Output: data/results/sensitivity_results.json
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats

# Local imports matching API surface
from config import get_project_root, get_data_path
from analysis.permutation import run_permutation_test, calculate_effect_size

logger = logging.getLogger(__name__)

def load_complexity_scores() -> pd.DataFrame:
    """Load the final complexity scores CSV."""
    root = get_project_root()
    path = root / "data" / "processed" / "complexity_scores.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    df = pd.read_csv(path)
    return df

def load_aggregated_d_scores() -> pd.DataFrame:
    """Load the aggregated D-scores CSV."""
    root = get_project_root()
    path = root / "data" / "processed" / "aggregated_d_scores.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    df = pd.read_csv(path)
    return df

def re_categorize_complexity(df: pd.DataFrame, metric: str = "edge_density", shift_sd: float = 0.0) -> pd.DataFrame:
    """
    Re-categorize complexity based on a shifted median threshold.

    The original logic (T018) uses the median of the metric to split Low/High.
    Here, we shift that median threshold by `shift_sd` (in units of SD).
    """
    if df.empty:
        return df

    # Calculate original median and SD
    values = df[metric].dropna()
    if len(values) == 0:
        return df

    median_val = np.median(values)
    std_val = np.std(values, ddof=1)

    if std_val == 0:
        # If no variance, shift has no effect, but we still return the dataframe
        logger.warning(f"Standard deviation of {metric} is 0. Shift applied will have no effect.")

    new_threshold = median_val + (shift_sd * std_val)

    # Apply new categorization
    # Logic: <= threshold -> Low, > threshold -> High
    df = df.copy()
    df['complexity_category_shifted'] = df[metric].apply(
        lambda x: 'Low' if x <= new_threshold else 'High'
    )

    # Store the threshold used for logging/debugging
    df['_threshold_used'] = new_threshold

    return df

def join_with_d_scores(complexity_df: pd.DataFrame, d_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join complexity data with D-scores.
    We need to map the session complexity condition to the D-score.
    The D-score CSV has 'complexity_condition' which might be the original.
    We will re-join based on the new categorization.
    """
    # Ensure we have participant_id and session_id in both
    # complexity_df has filename, we need to map filename to session_id or participant_id?
    # Looking at T026b schema: 'participant_id', 'session_id', 'complexity_condition'.
    # Looking at T017c schema: 'filename', 'complexity_category'.
    # We need a mapping between filename and session_id.
    # Assuming the filename in complexity_scores.csv corresponds to the stimulus used in the session.
    # However, the D-score aggregation (T026b) usually aggregates per session.
    # The task T035a says "re-run analysis". This implies we need to re-assign the condition
    # for each session based on the new threshold.

    # Let's assume the 'filename' in complexity_scores.csv is unique per stimulus.
    # And the 'session_id' in aggregated_d_scores.csv is associated with a specific stimulus filename.
    # If the D-score file doesn't have 'filename', we might need to infer it or assume
    # the 'complexity_condition' in D-score file is the ground truth we are perturbing.
    # Actually, the standard approach for this sensitivity analysis is:
    # 1. Take the raw stimulus metrics.
    # 2. Change the definition of "Low" vs "High" (the threshold).
    # 3. Re-assign the condition label to each session.
    # 4. Re-calculate the D-score difference.

    # We need to link the two tables.
    # If aggregated_d_scores.csv does not have 'filename', we must assume the 'complexity_condition'
    # column there is the one we are replacing.
    # But we need to know WHICH stimulus belongs to WHICH session to re-assign.
    # Let's assume the 'filename' column exists in aggregated_d_scores.csv or can be joined via participant_id/session_id.
    # If not present, we might need to look at the raw logs, but that's too complex for this step.
    # Let's assume the D-score file has a 'stimulus_filename' or we can join on 'session_id' if
    # the complexity file has 'session_id'.
    # T017c output: 'filename', ...
    # T026b output: 'participant_id', 'session_id', ...

    # Correction: The task T017c produces complexity_scores.csv.
    # The task T026b produces aggregated_d_scores.csv.
    # There must be a link. Usually, the session is run with a specific image.
    # If the link is missing, we cannot do this accurately.
    # However, looking at T026b description: "link and output paired session data".
    # Let's assume the `aggregated_d_scores.csv` has a column `stimulus_filename` or similar.
    # If not, we will try to join on a common key. If the key is missing, we raise an error.

    # Attempt to find a join key.
    common_cols = set(complexity_df.columns).intersection(set(d_scores_df.columns))
    if 'filename' in d_scores_df.columns:
        join_key = 'filename'
    elif 'stimulus_filename' in d_scores_df.columns:
        join_key = 'stimulus_filename'
    else:
        # Fallback: try to join on participant_id and session_id if complexity_df has them?
        # T017c schema: filename, edge_density, entropy, fractal_dim, complexity_category, status.
        # It does NOT have participant_id.
        # This implies the complexity file is stimulus-level, and D-score is session-level.
        # We need to know which stimulus was used in which session.
        # If that mapping is not in the CSVs, we must assume the D-score file's 'complexity_condition'
        # is the one to be replaced, but we can't re-assign without the mapping.
        # Wait, T035a says: "Read complexity_scores.csv ... to calculate SD ... re-run analysis".
        # This implies the analysis is on the stimulus-level grouping.
        # Perhaps the "analysis" here is simply re-grouping the stimuli and seeing how the D-scores
        # (which are already computed per session) distribute?
        # No, D-scores are per session. If we change the condition of a session, we change the grouping.
        # We MUST have the mapping.
        # Let's assume the `aggregated_d_scores.csv` has a column `stimulus_filename` that was added in T026b
        # but not explicitly listed in the schema description (or it's implied).
        # If not, we will try to join on 'session_id' if complexity_df has it.
        # Since T017c does not have session_id, we are stuck unless the D-score file has the filename.
        # Let's assume the D-score file has `stimulus_filename`. If not, we try `filename`.
        if 'filename' in d_scores_df.columns:
            join_key = 'filename'
        else:
            raise ValueError("Cannot join complexity and D-score data. Missing common key (filename or stimulus_filename).")

    merged = pd.merge(d_scores_df, complexity_df[['filename', 'complexity_category_shifted', '_threshold_used']],
                      left_on=join_key, right_on='filename', how='left')
    
    # Rename the new category column
    merged['complexity_condition'] = merged['complexity_category_shifted']
    
    # Drop helper columns
    merged = merged.drop(columns=['complexity_category_shifted', '_threshold_used', 'complexity_category'], errors='ignore')
    
    return merged

def run_analysis_for_threshold(shift_sd: float, complexity_df: pd.DataFrame, d_scores_df: pd.DataFrame) -> Dict[str, Any]:
    """Run the permutation test for a specific threshold shift."""
    logger.info(f"Running analysis for shift: {shift_sd:.2f} SD")

    # Re-categorize
    cat_df = re_categorize_complexity(complexity_df, shift_sd=shift_sd)

    # Join
    try:
        merged_df = join_with_d_scores(cat_df, d_scores_df)
    except Exception as e:
        logger.error(f"Failed to join data for shift {shift_sd}: {e}")
        return {
            "shift_sd": shift_sd,
            "status": "invalid",
            "reason": f"Join failed: {str(e)}"
        }

    # Filter valid D-scores
    valid_df = merged_df.dropna(subset=['d_score']).copy()
    valid_df = valid_df[valid_df['status'] == 'valid'] # Assuming 'valid' status from T026b

    # Group by new condition
    low_group = valid_df[valid_df['complexity_condition'] == 'Low']['d_score'].dropna()
    high_group = valid_df[valid_df['complexity_condition'] == 'High']['d_score'].dropna()

    n_low = len(low_group)
    n_high = len(high_group)

    # Check minimum N
    if n_low < 15 or n_high < 15:
        logger.warning(f"Insufficient samples for shift {shift_sd}: Low={n_low}, High={n_high}")
        return {
            "shift_sd": shift_sd,
            "status": "invalid",
            "n_low": int(n_low),
            "n_high": int(n_high),
            "reason": f"Sample size < 15 per condition (Low={n_low}, High={n_high})"
        }

    # Run permutation test
    try:
        # Use the logic from T033
        observed_diff = np.mean(high_group) - np.mean(low_group)
        p_value, effect_size, _ = run_permutation_test(
            low_group.values, high_group.values, 
            n_permutations=1000, 
            seed=42
        )
        
        return {
            "shift_sd": shift_sd,
            "status": "valid",
            "n_low": int(n_low),
            "n_high": int(n_high),
            "observed_diff": float(observed_diff),
            "p_value": float(p_value),
            "effect_size": float(effect_size)
        }
    except Exception as e:
        logger.error(f"Permutation test failed for shift {shift_sd}: {e}")
        return {
            "shift_sd": shift_sd,
            "status": "invalid",
            "reason": f"Permutation test error: {str(e)}"
        }

def run_sensitivity_analysis() -> Dict[str, Any]:
    """Main entry point for T035a."""
    logger.info("Starting Sensitivity Analysis (Threshold Sweep)")
    
    # Load data
    complexity_df = load_complexity_scores()
    d_scores_df = load_aggregated_d_scores()
    
    # Calculate SD of the metric (edge_density)
    metric = "edge_density"
    if metric not in complexity_df.columns:
        raise ValueError(f"Metric '{metric}' not found in complexity_scores.csv")
    
    std_val = complexity_df[metric].std()
    if std_val == 0:
        raise ValueError(f"Standard deviation of {metric} is 0. Cannot perform shift.")
    
    logger.info(f"Calculated SD for {metric}: {std_val:.4f}")
    
    # Define shifts
    shifts = [-0.15, -0.10, -0.05, 0.05, 0.10, 0.15]
    
    results = []
    for shift in shifts:
        result = run_analysis_for_threshold(shift, complexity_df, d_scores_df)
        results.append(result)
    
    # Aggregate results
    output = {
        "methodology": "Threshold Sweep Sensitivity Analysis",
        "metric": metric,
        "sd_value": float(std_val),
        "shifts_tested": shifts,
        "results": results
    }
    
    # Save to file
    root = get_project_root()
    out_path = root / "data" / "results" / "sensitivity_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Sensitivity analysis results saved to {out_path}")
    return output

def main():
    """CLI entry point."""
    setup_logging()
    result = run_sensitivity_analysis()
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
