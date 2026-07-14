import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis, load_datasets_from_raw
from cleaning import apply_iqr_outlier_removal
from config import get_config

# Ensure setup_logging is called early
logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    group_col: str, 
    outcome_col: str, 
    threshold: float = 0.05
) -> bool:
    """
    Estimate if a test on a null dataset (outcome shuffled) yields p <= threshold.
    Returns True if false positive (p <= threshold), False otherwise.
    """
    # Shuffle outcome to create null hypothesis
    df_null = df.copy()
    df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
    
    # Run t-test
    if group_col not in df_null.columns or outcome_col not in df_null.columns:
        return False
    
    df_clean = df_null[[group_col, outcome_col]].dropna()
    if df_clean.empty or df_clean[group_col].nunique() < 2:
        return False

    groups = df_clean.groupby(group_col)[outcome_col]
    g1 = groups.first()
    g2 = groups.last()

    t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
    return p_val <= threshold

def calculate_inconsistency_rate(
    baseline_p: float, 
    cleaned_p: float, 
    threshold: float = 0.05
) -> bool:
    """
    Calculate if significance status changed between baseline and cleaned.
    Returns True if inconsistency (status changed), False otherwise.
    """
    base_sig = baseline_p <= threshold
    clean_sig = cleaned_p <= threshold
    return base_sig != clean_sig

def run_threshold_sweep(
    k_values: List[float],
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    raw_data_dir: str,
    outcome_col: str = "target",
    group_col: str = "group",
    n_permutations: int = 100
) -> List[Dict[str, Any]]:
    """
    Run outlier threshold sweep for k in k_values.
    Calculates FPR and Inconsistency Rate per threshold.
    """
    logger = logging.getLogger(__name__)
    results = []
    
    # Load datasets for permutation test
    datasets = load_datasets_from_raw(raw_data_dir)
    if not datasets:
        logger.warning("No datasets found for permutation test")
        return results

    for k in k_values:
        logger.info(f"Sweeping threshold k={k}")
        
        fpr_count = 0
        total_perm_tests = 0
        inconsistency_count = 0
        total_datasets = 0

        # 1. Calculate FPR using permutation null datasets
        for df in datasets:
            # Ensure we have group and outcome
            if group_col not in df.columns or outcome_col not in df.columns:
                continue
            
            for _ in range(n_permutations):
                if estimate_fpr_for_dataset(df, group_col, outcome_col, threshold=0.05):
                    fpr_count += 1
                total_perm_tests += 1

        # 2. Calculate Inconsistency Rate using baseline vs cleaned metrics
        if baseline_metrics and cleaned_metrics:
            base_datasets = baseline_metrics.get("baseline", {}).get("datasets", [])
            # We need to match cleaned datasets to baseline. 
            # For this task, we assume we are comparing the same dataset processed with strategy k.
            # Since cleaned_metrics might contain multiple strategies, we look for matching dataset names.
            
            for base_entry in base_datasets:
                ds_name = base_entry.get("dataset_name")
                base_p = base_entry.get("t_test", {}).get("p_value")
                
                if base_p is None or np.isnan(base_p):
                    continue
                
                # Find corresponding cleaned entry (simplified: assume first match or specific strategy)
                # In a real scenario, we'd match by strategy name containing 'k={k}'
                clean_entry = None
                for c_entry in cleaned_metrics.get("cleaned", {}).get("datasets", []):
                    if c_entry.get("dataset_name") == ds_name:
                        clean_entry = c_entry
                        break
                
                if clean_entry:
                    clean_p = clean_entry.get("t_test", {}).get("p_value")
                    if clean_p is not None and not np.isnan(clean_p):
                        if calculate_inconsistency_rate(base_p, clean_p, threshold=0.05):
                            inconsistency_count += 1
                total_datasets += 1

        fpr = fpr_count / total_perm_tests if total_perm_tests > 0 else 0.0
        inconsistency_rate = inconsistency_count / total_datasets if total_datasets > 0 else 0.0

        results.append({
            "k_value": k,
            "fpr": fpr,
            "inconsistency_rate": inconsistency_rate,
            "n_permutations": total_perm_tests,
            "n_datasets": total_datasets
        })

    return results

def write_output(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write sweep results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "sweep_results": results
    }
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Wrote outlier threshold sweep results to {output_path}")

def main():
    config = get_config()
    pin_random_seed(config.get("RANDOM_SEED", 42))
    
    baseline_path = os.path.join(config.get("PROCESSED_DATA_PATH", "data/processed"), "baseline_metrics.json")
    cleaned_path = os.path.join(config.get("PROCESSED_DATA_PATH", "data/processed"), "cleaned_metrics.json")
    output_path = os.path.join(config.get("PROCESSED_DATA_PATH", "data/processed"), "outlier_threshold_sweep.json")
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")

    # Load metrics
    baseline_metrics = load_baseline_metrics(baseline_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_path)

    # Define k values to sweep
    k_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    # Run sweep
    results = run_threshold_sweep(
        k_values=k_values,
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics,
        raw_data_dir=raw_dir,
        outcome_col="target",
        group_col="group",
        n_permutations=100
    )

    # Write output
    write_output(results, output_path)

    logger.info("Outlier threshold sweep completed.")

if __name__ == "__main__":
    main()