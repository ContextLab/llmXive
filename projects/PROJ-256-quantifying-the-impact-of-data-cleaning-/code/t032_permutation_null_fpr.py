"""
T032: Implement permutation null dataset generation for false-positive rate (FPR) estimation.

Requirement: Generate null datasets by shuffling outcomes while keeping predictors fixed.
Output: data/processed/null_fpr_metrics.json
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis, analyze_dataset

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(filepath: str) -> pd.DataFrame:
    """Load a dataset from the processed directory."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    return pd.read_csv(filepath)

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable while keeping predictors fixed.
    This breaks any true relationship between predictors and outcome.
    """
    pin_random_seed(random_seed)
    null_df = df.copy()
    null_df[outcome_col] = np.random.permutation(null_df[outcome_col].values)
    return null_df

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    outcome_col: str, 
    group_col: str, 
    n_permutations: int = 100, 
    alpha: float = 0.05,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate (FPR) for a dataset using permutation testing.
    FPR is the proportion of permuted datasets where p <= alpha (incorrectly rejecting null).
    """
    pin_random_seed(random_seed)
    significant_count = 0
    p_values = []
    
    for i in range(n_permutations):
        null_df = generate_null_dataset(df, outcome_col, random_seed=random_seed + i)
        try:
            result = analyze_dataset(null_df, f"null_perm_{i}", outcome_col, group_col)
            p_val = result["t_test"]["p_value"]
            p_values.append(p_val)
            if p_val <= alpha:
                significant_count += 1
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}")
            continue
    
    fpr = significant_count / n_permutations if n_permutations > 0 else 0.0
    
    return {
        "fpr": float(fpr),
        "significant_count": significant_count,
        "total_permutations": n_permutations,
        "alpha": alpha,
        "p_values": p_values,
        "mean_p_value": float(np.mean(p_values)) if p_values else 0.0,
        "median_p_value": float(np.median(p_values)) if p_values else 0.0
    }

def write_output(metrics: Dict[str, Any], output_path: str) -> bool:
    """Write FPR metrics to JSON file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        logger.info(f"Written FPR metrics to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False

def main():
    """Main entry point for permutation null FPR estimation."""
    logger.info("Starting permutation null FPR estimation (T032)")
    
    # Configuration
    baseline_metrics_path = "data/processed/baseline_metrics.json"
    processed_dir = "data/processed"
    output_file = "data/processed/null_fpr_metrics.json"
    outcome_col = "outcome"
    group_col = "group"
    n_permutations = 100
    alpha = 0.05
    random_seed = 42
    
    # Load baseline metrics to get dataset info
    try:
        baseline_metrics = load_baseline_metrics(baseline_metrics_path)
    except Exception as e:
        logger.error(f"Failed to load baseline metrics: {e}")
        sys.exit(1)
    
    if not baseline_metrics or "datasets" not in baseline_metrics:
        logger.error("No baseline metrics found. Cannot proceed with FPR estimation.")
        # Create empty output if no data
        empty_output = {
            "timestamp": datetime.now().isoformat(),
            "description": "No baseline datasets available for FPR estimation",
            "datasets": [],
            "global_fpr": None
        }
        write_output(empty_output, output_file)
        return 1
    
    fpr_results = []
    total_significant = 0
    total_tests = 0
    
    for dataset_entry in baseline_metrics.get("datasets", []):
        dataset_name = dataset_entry.get("dataset_name", "unknown")
        logger.info(f"Processing FPR for dataset: {dataset_name}")
        
        # We need the actual DataFrame to permute. 
        # If the baseline entry has a path, use it. Otherwise, we might need to re-load from raw.
        # For now, we assume we can reconstruct or we skip if data not available.
        # In a real pipeline, the raw data should be accessible.
        
        # Try to find the dataset in raw/processed
        possible_paths = [
            os.path.join(processed_dir, f"{dataset_name}.csv"),
            os.path.join("data/raw", f"{dataset_name}.csv"),
            os.path.join("data/processed", f"{dataset_name}_cleaned.csv")
        ]
        
        df = None
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    logger.info(f"Loaded dataset from {path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")
        
        if df is None:
            logger.warning(f"Could not find data for {dataset_name}, skipping FPR estimation.")
            continue
        
        # Estimate FPR
        fpr_result = estimate_fpr_for_dataset(
            df, 
            outcome_col, 
            group_col, 
            n_permutations=n_permutations,
            alpha=alpha,
            random_seed=random_seed
        )
        
        fpr_result["dataset_name"] = dataset_name
        fpr_results.append(fpr_result)
        
        total_significant += fpr_result["significant_count"]
        total_tests += fpr_result["total_permutations"]
    
    # Calculate global FPR
    global_fpr = total_significant / total_tests if total_tests > 0 else 0.0
    
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "description": "False Positive Rate estimation via permutation testing (outcome shuffled)",
        "parameters": {
            "n_permutations": n_permutations,
            "alpha": alpha,
            "random_seed": random_seed
        },
        "global_fpr": global_fpr,
        "datasets": fpr_results
    }
    
    success = write_output(output_data, output_file)
    
    if success:
        logger.info(f"FPR estimation complete. Global FPR: {global_fpr:.4f}")
        return 0
    else:
        logger.error("Failed to write FPR metrics.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
