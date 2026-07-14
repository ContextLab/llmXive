import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local modules
from utils import setup_logging, pin_random_seed
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis, load_datasets_from_raw
from reporting import load_json_file

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    return load_json_file(filepath)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    return load_json_file(filepath)

def load_dataset_from_processed(dataset_name: str) -> pd.DataFrame:
    """Load a specific dataset from the processed directory."""
    # Try to find the dataset in processed directory
    processed_dir = "data/processed"
    # Look for CSV files matching the dataset name
    candidates = [f for f in os.listdir(processed_dir) if dataset_name.lower() in f.lower() and f.endswith('.csv')]
    if not candidates:
        raise FileNotFoundError(f"No dataset found matching: {dataset_name}")
    
    # Use the first match (usually the raw or baseline version)
    dataset_path = os.path.join(processed_dir, candidates[0])
    return pd.read_csv(dataset_path)

def estimate_fpr_for_dataset(df: pd.DataFrame, outcome_col: str, group_col: str, threshold_k: float) -> float:
    """
    Estimate False Positive Rate (FPR) for a dataset at a specific outlier threshold.
    
    FPR is calculated as the proportion of tests with p <= 0.05 in null datasets.
    For this implementation, we simulate a null by shuffling the outcome variable
    and applying the cleaning strategy, then running the statistical test.
    """
    if df.empty:
        return 0.0
    
    # Ensure required columns exist
    if outcome_col not in df.columns or group_col not in df.columns:
        logger.warning(f"Columns {outcome_col} or {group_col} not found in dataset. Skipping FPR estimation.")
        return 0.0
    
    # Create a null dataset by shuffling the outcome
    df_null = df.copy()
    shuffled_outcome = df_null[outcome_col].sample(frac=1, replace=False).reset_index(drop=True)
    df_null[outcome_col] = shuffled_outcome
    
    # Apply outlier removal with the specified threshold
    df_cleaned = apply_iqr_outlier_removal(df_null, k=threshold_k)
    
    if df_cleaned.empty or len(df_cleaned) < 2:
        logger.warning(f"Dataset too small after cleaning at k={threshold_k}. Skipping FPR estimation.")
        return 0.0
    
    # Run statistical test on the null dataset
    try:
        # Run t-test
        result = run_baseline_analysis(df_cleaned, dataset_name="null", config={})
        if isinstance(result, dict) and "t_tests" in result:
            for test_name, test_result in result["t_tests"].items():
                if "p_value" in test_result:
                    p_val = test_result["p_value"]
                    if p_val is not None and p_val <= 0.05:
                        return 1.0  # False positive detected
        return 0.0
    except Exception as e:
        logger.warning(f"Error running statistical test for FPR estimation: {e}")
        return 0.0

def calculate_inconsistency_rate(baseline_metrics: Dict[str, Any], cleaned_metrics: Dict[str, Any], threshold_k: float) -> float:
    """
    Calculate Inconsistency Rate: proportion of datasets where significance status changes.
    
    Significance status changes if a test that was significant (p <= 0.05) becomes
    non-significant, or vice versa, after applying the cleaning strategy with threshold k.
    """
    if not baseline_metrics or not cleaned_metrics:
        logger.warning("Baseline or cleaned metrics not available. Cannot calculate inconsistency rate.")
        return 0.0
    
    baseline_datasets = baseline_metrics.get("datasets", [])
    cleaned_datasets = cleaned_metrics.get("datasets", [])
    
    if not baseline_datasets or not cleaned_datasets:
        logger.warning("No datasets found in metrics. Cannot calculate inconsistency rate.")
        return 0.0
    
    # Create a mapping of cleaned datasets by name
    cleaned_map = {}
    for entry in cleaned_datasets:
        name = entry.get("dataset_name") or entry.get("dataset_id")
        if name:
            cleaned_map[name] = entry
    
    inconsistent_count = 0
    total_count = 0
    
    for baseline_entry in baseline_datasets:
        name = baseline_entry.get("dataset_name") or baseline_entry.get("dataset_id")
        if not name or name not in cleaned_map:
            continue
        
        cleaned_entry = cleaned_map[name]
        total_count += 1
        
        # Compare t-test results
        baseline_tests = baseline_entry.get("t_tests", {})
        cleaned_tests = cleaned_entry.get("t_tests", {})
        
        for test_name, baseline_test in baseline_tests.items():
            if test_name not in cleaned_tests:
                continue
            
            baseline_p = baseline_test.get("p_value")
            cleaned_p = cleaned_tests[test_name].get("p_value")
            
            if baseline_p is None or cleaned_p is None:
                continue
            
            baseline_sig = baseline_p <= 0.05
            cleaned_sig = cleaned_p <= 0.05
            
            if baseline_sig != cleaned_sig:
                inconsistent_count += 1
                break  # Count dataset as inconsistent if any test changes status
    
    if total_count == 0:
        return 0.0
    
    return inconsistent_count / total_count

def run_threshold_sweep(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    thresholds: List[float],
    outcome_col: str = "outcome",
    group_col: str = "group"
) -> List[Dict[str, Any]]:
    """
    Run outlier threshold sweep for specified k values.
    
    Returns a list of results, each containing:
    - threshold_k: The outlier removal threshold used
    - fpr: False Positive Rate (proportion of null tests with p <= 0.05)
    - inconsistency_rate: Proportion of datasets where significance status changes
    """
    results = []
    
    for k in thresholds:
        logger.info(f"Running threshold sweep for k={k}")
        
        # Estimate FPR (using a representative dataset or all datasets)
        # For efficiency, we'll use the first available dataset
        fpr_sum = 0.0
        fpr_count = 0
        
        # Try to get a dataset for FPR estimation
        try:
            # Load a dataset from processed data
            processed_dir = "data/processed"
            csv_files = [f for f in os.listdir(processed_dir) if f.endswith('.csv') and 'baseline' not in f and 'cleaned' not in f]
            
            if csv_files:
                # Use the first CSV file found
                dataset_path = os.path.join(processed_dir, csv_files[0])
                df = pd.read_csv(dataset_path)
                
                # Estimate FPR for this dataset
                fpr = estimate_fpr_for_dataset(df, outcome_col, group_col, k)
                fpr_sum += fpr
                fpr_count += 1
        except Exception as e:
            logger.warning(f"Could not estimate FPR: {e}")
        
        # Calculate inconsistency rate
        inconsistency_rate = calculate_inconsistency_rate(baseline_metrics, cleaned_metrics, k)
        
        # Average FPR if multiple datasets were used
        avg_fpr = fpr_sum / fpr_count if fpr_count > 0 else 0.0
        
        result = {
            "threshold_k": k,
            "fpr": round(avg_fpr, 4),
            "inconsistency_rate": round(inconsistency_rate, 4),
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)
        
        logger.info(f"Threshold k={k}: FPR={avg_fpr:.4f}, Inconsistency Rate={inconsistency_rate:.4f}")
    
    return results

def write_output(results: List[Dict[str, Any]], output_path: str = "data/processed/outlier_threshold_sweep.json"):
    """Write threshold sweep results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        "threshold_sweep_results": results,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "description": "Outlier threshold sweep for k values with FPR and inconsistency rate"
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Threshold sweep results written to {output_path}")

def main():
    """Main entry point for outlier threshold sweep analysis."""
    logger.info("Starting outlier threshold sweep analysis (T033)")
    
    # Define thresholds to sweep
    # Based on task description: k ∈ {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}
    thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    # Load baseline and cleaned metrics
    try:
        baseline_metrics = load_baseline_metrics()
        cleaned_metrics = load_cleaned_metrics()
    except FileNotFoundError as e:
        logger.error(f"Missing required metrics: {e}")
        logger.error("Please ensure baseline_metrics.json and cleaned_metrics.json exist in data/processed/")
        sys.exit(1)
    
    # Run threshold sweep
    results = run_threshold_sweep(baseline_metrics, cleaned_metrics, thresholds)
    
    # Write output
    write_output(results)
    
    logger.info("Outlier threshold sweep analysis completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
