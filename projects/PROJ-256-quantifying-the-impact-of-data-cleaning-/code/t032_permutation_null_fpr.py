"""
T032: Implement permutation null dataset generation for false-positive rate (FPR) estimation.

Requirement: Generate null datasets by shuffling outcomes while keeping predictors fixed.
Output: data/processed/null_fpr_metrics.json
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis, load_datasets_from_raw

def load_baseline_metrics(filepath: str) -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(filepath: str) -> pd.DataFrame:
    """Load dataset from processed directory."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    return pd.read_csv(filepath)

def generate_null_dataset(df: pd.DataFrame, outcome_col: str) -> pd.DataFrame:
    """
    Generate null dataset by shuffling outcome variable.
    
    Args:
        df: Original DataFrame
        outcome_col: Name of outcome column to shuffle
        
    Returns:
        DataFrame with shuffled outcome
    """
    df_null = df.copy()
    if outcome_col not in df_null.columns:
        raise ValueError(f"Outcome column {outcome_col} not found in DataFrame")
    
    # Shuffle outcome while keeping predictors fixed
    df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
    return df_null

def estimate_fpr_for_dataset(
    df_null: pd.DataFrame, 
    outcome_col: str, 
    group_col: str,
    significance_level: float = 0.05
) -> bool:
    """
    Estimate if a null dataset produces a false positive.
    
    Args:
        df_null: Null dataset with shuffled outcome
        outcome_col: Outcome column name
        group_col: Group column name
        significance_level: Significance threshold
        
    Returns:
        True if p-value <= significance_level (false positive)
    """
    from scipy import stats
    
    # Ensure columns exist
    if outcome_col not in df_null.columns or group_col not in df_null.columns:
        return False
    
    # Drop missing values
    df_clean = df_null[[outcome_col, group_col]].dropna()
    
    if df_clean[group_col].nunique() != 2:
        return False
    
    groups = df_clean[group_col].unique()
    group1_data = df_clean[df_clean[group_col] == groups[0]][outcome_col]
    group2_data = df_clean[df_clean[group_col] == groups[1]][outcome_col]
    
    if len(group1_data) < 2 or len(group2_data) < 2:
        return False
    
    t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
    
    return p_value <= significance_level

def write_output(results: Dict[str, Any], output_path: str) -> None:
    """Write results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Null FPR metrics written to {output_path}")

def main():
    """Main entry point for permutation null FPR estimation."""
    pin_random_seed(42)
    
    # Configuration
    baseline_metrics_path = "data/processed/baseline_metrics.json"
    processed_dir = "data/processed"
    output_path = "data/processed/null_fpr_metrics.json"
    significance_level = 0.05
    n_permutations = 100  # Number of permutations per dataset
    
    logger.info("Starting permutation null FPR estimation")
    
    # Load baseline metrics to get dataset info
    try:
        baseline_metrics = load_baseline_metrics(baseline_metrics_path)
    except Exception as e:
        logger.error(f"Failed to load baseline metrics: {e}")
        sys.exit(1)
    
    datasets = baseline_metrics.get("datasets", [])
    if not datasets:
        logger.error("No datasets found in baseline metrics")
        sys.exit(1)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "n_permutations": n_permutations,
        "significance_level": significance_level,
        "dataset_results": []
    }
    
    # Process each dataset
    for ds in datasets:
        dataset_name = ds.get("dataset_name")
        if not dataset_name:
            continue
        
        # Find corresponding CSV file in processed directory
        csv_files = [f for f in os.listdir(processed_dir) 
                    if f.startswith(dataset_name) and f.endswith('.csv')]
        
        if not csv_files:
            logger.warning(f"No processed CSV found for {dataset_name}, skipping")
            continue
        
        csv_path = os.path.join(processed_dir, csv_files[0])
        
        try:
            df = load_dataset_from_processed(csv_path)
            
            # Determine columns
            outcome_col = None
            group_col = None
            
            # Try to infer columns from baseline results
            if ds.get("t_test"):
                # Infer from t_test structure if possible
                # For now, use common column names
                if "outcome" in df.columns:
                    outcome_col = "outcome"
                elif "target" in df.columns:
                    outcome_col = "target"
                elif df.select_dtypes(include=[np.number]).iloc[:, -1].name:
                    outcome_col = df.select_dtypes(include=[np.number]).iloc[:, -1].name
                
                if "group" in df.columns:
                    group_col = "group"
                elif "category" in df.columns:
                    group_col = "category"
                elif df.select_dtypes(include=['object']).iloc[:, 0].name if not df.select_dtypes(include=['object']).empty else None:
                    group_col = df.select_dtypes(include=['object']).iloc[:, 0].name
            
            if not outcome_col or not group_col:
                logger.warning(f"Could not determine outcome/group columns for {dataset_name}, skipping")
                continue
            
            # Run permutations
            fp_count = 0
            for i in range(n_permutations):
                df_null = generate_null_dataset(df, outcome_col)
                is_fp = estimate_fpr_for_dataset(df_null, outcome_col, group_col, significance_level)
                if is_fp:
                    fp_count += 1
            
            fpr = fp_count / n_permutations
            
            dataset_result = {
                "dataset_name": dataset_name,
                "n_permutations": n_permutations,
                "false_positives": fp_count,
                "fpr": round(fpr, 4),
                "outcome_column": outcome_col,
                "group_column": group_col
            }
            
            results["dataset_results"].append(dataset_result)
            logger.info(f"  {dataset_name}: FPR = {fpr:.4f} ({fp_count}/{n_permutations})")
            
        except Exception as e:
            logger.error(f"Error processing {dataset_name}: {e}")
            continue
    
    # Calculate overall FPR
    if results["dataset_results"]:
        overall_fpr = sum(r["fpr"] for r in results["dataset_results"]) / len(results["dataset_results"])
        results["overall_fpr"] = round(overall_fpr, 4)
        logger.info(f"Overall FPR: {overall_fpr:.4f}")
    
    # Write output
    write_output(results, output_path)
    
    logger.info("Permutation null FPR estimation completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
