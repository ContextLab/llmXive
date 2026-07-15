import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np

from logging_config import setup_logger, get_logger
from state_tracker import update_state_with_artifact, load_state_file, save_state_file

# Initialize logger
logger = get_logger("run_bh_correction")

def load_metrics_data(metrics_dir: Path) -> dict:
    """
    Load metric CSV files from the metrics directory.
    Returns a dictionary mapping metric name to a DataFrame.
    """
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    metrics_data = {}
    for csv_file in metrics_dir.glob("*.csv"):
        metric_name = csv_file.stem
        try:
            df = pd.read_csv(csv_file)
            # Ensure we have the necessary columns for statistical analysis
            # Expected columns based on T023/T024: 'group', 'score' (or similar)
            # We need to extract the scores for each group to compute p-values if not present
            # However, T028/T029 implies p-values and effect sizes are computed.
            # We assume T028 output a file with p-values or we need to recompute.
            # Given T028 is "run_mann_whitney_u_test", let's assume we need to aggregate results.
            # To be safe, we will look for a specific "statistical_results" file or
            # re-compute from raw metrics if a pre-computed p-value file isn't found.
            #
            # Strategy:
            # 1. Check if a file named 'mann_whitney_results.csv' or similar exists.
            # 2. If not, we must compute p-values from the raw metric data (group, score).
            #
            # Let's assume the raw metric data is in these CSVs with columns:
            # 'snippet_id', 'group' (human/llm), 'score' (or metric_name)
            # We will aggregate these to compute p-values if needed.
            #
            # Actually, T028/T029 tasks imply they produced results.
            # Let's look for a file containing the p-values first.
            # If not found, we compute on the fly from the raw data.
            metrics_data[metric_name] = df
        except Exception as e:
            logger.warning(f"Could not load {csv_file}: {e}")
    
    return metrics_data

def apply_benjamini_hochberg(p_values: list, names: list) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Parameters:
    - p_values: List of raw p-values
    - names: List of corresponding metric names (or hypothesis names)
    
    Returns:
    - DataFrame with columns: 'metric', 'raw_p', 'adjusted_p', 'significant'
    """
    if not p_values:
        return pd.DataFrame(columns=['metric', 'raw_p', 'adjusted_p', 'significant'])
    
    n = len(p_values)
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    sorted_names = [names[i] for i in sorted_indices]
    
    # Compute BH critical values
    # rank goes from 1 to n
    ranks = np.arange(1, n + 1)
    # BH threshold: (rank / n) * alpha. We want to find the largest k such that p(k) <= (k/n)*alpha
    # But for adjustment, we calculate adjusted p = min(p * n / rank, 1)
    # We also need to ensure monotonicity from the top down (adjusted_p[i] <= adjusted_p[i+1])
    
    adjusted_p = sorted_p * n / ranks
    
    # Ensure adjusted p-values are within [0, 1]
    adjusted_p = np.clip(adjusted_p, 0.0, 1.0)
    
    # Enforce monotonicity: adjusted_p[i] <= adjusted_p[i+1]
    # We iterate backwards
    for i in range(n - 2, -1, -1):
        if adjusted_p[i] > adjusted_p[i + 1]:
            adjusted_p[i] = adjusted_p[i + 1]
    
    # Re-sort back to original order
    original_indices = np.argsort(sorted_indices)
    final_adjusted_p = adjusted_p[original_indices]
    
    result_df = pd.DataFrame({
        'metric': names,
        'raw_p': p_values,
        'adjusted_p': final_adjusted_p,
        'significant': [p < 0.05 for p in final_adjusted_p]
    })
    
    return result_df

def compute_p_values_from_raw_data(metrics_data: dict) -> list:
    """
    If p-values are not pre-computed, compute Mann-Whitney U p-values from raw data.
    Assumes each DataFrame has 'group' and 'score' columns.
    """
    from scipy.stats import mannwhitneyu
    
    p_values = []
    metric_names = []
    
    for metric_name, df in metrics_data.items():
        try:
            # Group by 'group' column
            if 'group' not in df.columns or 'score' not in df.columns:
                logger.warning(f"Skipping {metric_name}: missing 'group' or 'score' columns")
                continue
            
            human_scores = df[df['group'] == 'human']['score'].dropna()
            llm_scores = df[df['group'] == 'llm']['score'].dropna()
            
            if len(human_scores) == 0 or len(llm_scores) == 0:
                logger.warning(f"Skipping {metric_name}: insufficient data in one group")
                continue
            
            # Perform Mann-Whitney U test
            stat, p_val = mannwhitneyu(human_scores, llm_scores, alternative='two-sided')
            p_values.append(p_val)
            metric_names.append(metric_name)
        except Exception as e:
            logger.error(f"Error computing p-value for {metric_name}: {e}")
            continue
    
    return p_values, metric_names

def run_bh_correction_pipeline(metrics_dir: Path, output_dir: Path):
    """
    Main pipeline to load metrics, compute p-values if needed, apply BH correction,
    and save results.
    """
    logger.info("Starting Benjamini-Hochberg correction pipeline")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    metrics_data = load_metrics_data(metrics_dir)
    
    if not metrics_data:
        logger.error("No metric data found to process.")
        return
    
    # Try to find pre-computed p-values
    # T028 might have written a file like 'mann_whitney_results.csv'
    # If it exists, we use those p-values. Otherwise, we compute from raw data.
    p_val_file = metrics_dir.parent / "statistical_analysis" / "mann_whitney_results.csv"
    if not p_val_file.exists():
        # Check common locations
        p_val_file = metrics_dir.parent / "results" / "mann_whitney_results.csv"
    
    p_values = []
    metric_names = []
    
    if p_val_file.exists():
        logger.info(f"Loading pre-computed p-values from {p_val_file}")
        try:
            p_df = pd.read_csv(p_val_file)
            # Assume columns: 'metric', 'p_value'
            if 'metric' in p_df.columns and 'p_value' in p_df.columns:
                metric_names = p_df['metric'].tolist()
                p_values = p_df['p_value'].tolist()
            else:
                # Fallback to computing from raw data
                logger.warning("Pre-computed file format invalid. Computing from raw data.")
                p_values, metric_names = compute_p_values_from_raw_data(metrics_data)
        except Exception as e:
            logger.warning(f"Error reading p-value file: {e}. Computing from raw data.")
            p_values, metric_names = compute_p_values_from_raw_data(metrics_data)
    else:
        logger.info("No pre-computed p-values found. Computing from raw metric data.")
        p_values, metric_names = compute_p_values_from_raw_data(metrics_data)
    
    if not p_values:
        logger.error("No p-values could be computed or loaded.")
        return
    
    logger.info(f"Applying BH correction to {len(p_values)} metrics")
    bh_results = apply_benjamini_hochberg(p_values, metric_names)
    
    # Save results
    output_file = output_dir / "bh_corrected_pvalues.csv"
    bh_results.to_csv(output_file, index=False)
    logger.info(f"Saved BH corrected p-values to {output_file}")
    
    # Update state
    try:
        state_file = Path("state/projects/PROJ-488-evaluating-the-impact-of-code-generation.yaml")
        if state_file.exists():
            update_state_with_artifact(state_file, "bh_correction", str(output_file))
            logger.info("State updated with BH correction artifact.")
        else:
            logger.warning("State file not found. Skipping state update.")
    except Exception as e:
        logger.error(f"Failed to update state: {e}")
    
    return bh_results

def main():
    project_root = Path(__file__).parent.parent
    metrics_dir = project_root / "data" / "metrics"
    output_dir = project_root / "results" / "statistical_analysis"
    
    run_bh_correction_pipeline(metrics_dir, output_dir)

if __name__ == "__main__":
    main()
