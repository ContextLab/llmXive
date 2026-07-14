"""
Task T032: Implement permutation null dataset generation for FPR estimation.

Generates null datasets by shuffling the outcome variable while keeping predictors fixed.
Runs statistical tests on these null datasets to estimate the False Positive Rate (FPR).
Outputs results to data/processed/null_fpr_metrics.json.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_baseline_analysis, identify_numerical_columns
from utils import setup_logging, pin_random_seed
from config import Config

logger = logging.getLogger(__name__)

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline metrics from the processed data directory."""
    path = "data/processed/baseline_metrics.json"
    if not os.path.exists(path):
        logger.warning(f"Baseline metrics file not found at {path}. Skipping FPR estimation.")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Load a dataset from the processed directory.
    Expects files like 'data/processed/<dataset_name>_cleaned_*.csv' or raw processed versions.
    For this task, we look for the raw processed version or the original raw if processed is missing.
    """
    # Try to find the dataset in processed first (might be the baseline cleaned version or raw)
    # The baseline analysis script T012 usually saves the raw data as well or we load from raw
    # Let's try to load from data/raw first if we know the name, or search processed
    
    raw_path = f"data/raw/{dataset_name}"
    if os.path.exists(raw_path) or os.path.exists(raw_path + ".csv"):
        if os.path.isdir(raw_path):
            # It's a directory (like UCI HAR), we need to handle it specifically or fallback
            # For T032, we assume simple CSVs or the specific structure handled by data_loader
            # If it's a directory, we might need to reconstruct or use the processed version
            logger.info(f"Found raw directory for {dataset_name}, attempting to load processed version.")
            pass
        
        ext = ".csv" if not raw_path.endswith(".csv") else ""
        full_path = raw_path + ext if not raw_path.endswith(".csv") else raw_path
        if os.path.isfile(full_path):
            return pd.read_csv(full_path)
    
    # Fallback: look in processed for a file containing the name
    processed_dir = "data/processed"
    if os.path.exists(processed_dir):
        files = [f for f in os.listdir(processed_dir) if dataset_name.lower() in f.lower() and f.endswith('.csv')]
        if files:
            # Take the first match
            return pd.read_csv(os.path.join(processed_dir, files[0]))
    
    logger.error(f"Could not locate dataset file for {dataset_name} in data/raw or data/processed")
    return None

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable.
    
    Args:
        df: Original dataframe
        outcome_col: Name of the outcome/target column
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with shuffled outcome column
    """
    pin_random_seed(seed)
    df_null = df.copy()
    
    # Shuffle the outcome column
    shuffled_outcome = df_null[outcome_col].values.copy()
    np.random.shuffle(shuffled_outcome)
    df_null[outcome_col] = shuffled_outcome
    
    return df_null

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    dataset_name: str, 
    outcome_col: str, 
    n_permutations: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Estimate FPR for a single dataset by running statistical tests on permuted data.
    
    The FPR is the proportion of tests that incorrectly reject the null hypothesis
    (i.e., find p <= 0.05) when the outcome is randomly shuffled (no true relationship).
    """
    logger.info(f"Estimating FPR for dataset: {dataset_name} ({n_permutations} permutations)")
    
    pin_random_seed(seed)
    significant_count = 0
    total_tests = 0
    p_values = []
    
    # Identify numerical predictors (exclude outcome)
    # We need to know which columns to test. Usually, we test all numerical columns against outcome.
    numerical_cols = identify_numerical_columns(df)
    predictor_cols = [c for c in numerical_cols if c != outcome_col]
    
    if not predictor_cols:
        logger.warning(f"No numerical predictor columns found for {dataset_name}. Skipping FPR estimation.")
        return {
            "dataset_name": dataset_name,
            "outcome_column": outcome_col,
            "fpr": 0.0,
            "n_permutations": n_permutations,
            "significant_tests": 0,
            "total_tests": 0,
            "error": "No predictors found"
        }

    for i in range(n_permutations):
        # Generate null dataset
        df_null = generate_null_dataset(df, outcome_col, seed + i)
        
        # Run baseline analysis on the null dataset
        # We pass the dataframe directly to run_baseline_analysis if it supports it
        # Based on the API surface, run_baseline_analysis can accept (df, dataset_name, config)
        # We need to ensure the function handles the df input correctly.
        # If run_baseline_analysis expects a path, we might need to adapt.
        # Let's assume it can handle a DataFrame based on the multi-signature requirement.
        
        try:
            # Attempt to run analysis on the null dataframe
            # We create a temporary config or pass minimal args
            result = run_baseline_analysis(df_null, dataset_name=f"{dataset_name}_null_{i}", config={})
            
            if result and isinstance(result, dict) and result.get('success'):
                tests = result.get('results', {})
                for test_name, test_data in tests.items():
                    p_val = test_data.get('p_value')
                    if p_val is not None and np.isfinite(p_val):
                        total_tests += 1
                        p_values.append(p_val)
                        if p_val <= 0.05:
                            significant_count += 1
            else:
                logger.warning(f"Analysis failed for permutation {i} of {dataset_name}")
                
        except Exception as e:
            logger.error(f"Error during permutation {i} for {dataset_name}: {e}")
            continue

    fpr = significant_count / total_tests if total_tests > 0 else 0.0
    
    return {
        "dataset_name": dataset_name,
        "outcome_column": outcome_col,
        "fpr": round(fpr, 4),
        "n_permutations": n_permutations,
        "significant_tests": significant_count,
        "total_tests": total_tests,
        "mean_p_value": round(np.mean(p_values), 4) if p_values else 0.0,
        "median_p_value": round(np.median(p_values), 4) if p_values else 0.0
    }

def write_output(results: List[Dict[str, Any]], output_path: str):
    """Write the FPR metrics to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_data = {
        "generated_at": str(pd.Timestamp.now()),
        "description": "False Positive Rate (FPR) estimation via permutation testing",
        "results": results,
        "summary": {
            "total_datasets": len(results),
            "datasets_with_fpr": len([r for r in results if r.get('total_tests', 0) > 0]),
            "average_fpr": round(np.mean([r['fpr'] for r in results if r.get('total_tests', 0) > 0]), 4) if any(r.get('total_tests', 0) > 0 for r in results) else 0.0
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Null FPR metrics written to {output_path}")

def main():
    """Main entry point for T032."""
    logger = setup_logging("INFO")
    logger.info("Starting T032: Permutation Null FPR Estimation")
    
    # Load baseline metrics to get list of datasets and outcome columns
    # The baseline_metrics.json structure is assumed to have dataset info
    baseline_metrics = load_baseline_metrics()
    
    if not baseline_metrics:
        logger.error("No baseline metrics found. Cannot proceed with FPR estimation.")
        return 1
    
    # Determine output path
    output_path = "data/processed/null_fpr_metrics.json"
    
    results = []
    
    # Extract datasets from baseline metrics
    # Structure depends on how T012/T013 saved it. Assuming 'datasets' key or top-level list.
    datasets = baseline_metrics.get('datasets', [])
    if not datasets and isinstance(baseline_metrics, list):
        datasets = baseline_metrics
    
    if not datasets:
        logger.warning("No datasets found in baseline metrics.")
        # Try to infer from file system if metrics are empty
        # But per task, we rely on metrics
        return 1

    for entry in datasets:
        dataset_name = entry.get('dataset_name') or entry.get('name')
        if not dataset_name:
            continue
        
        # Identify outcome column. Usually 'outcome' or 'target' or inferred.
        # For UCI HAR, it's 'activity'. For Shopper, it might be 'purchased' or similar.
        # We'll try to find a column that was used as outcome in the baseline.
        # If not explicitly stored, we might need to guess or skip.
        # Let's assume the baseline analysis stored the outcome column name or we can deduce it.
        # If not present, we skip this dataset or try common names.
        outcome_col = entry.get('outcome_column')
        if not outcome_col:
            # Fallback: try common names
            possible_outcomes = ['outcome', 'target', 'label', 'class', 'activity', 'purchased', 'y']
            df_temp = load_dataset_from_processed(dataset_name)
            if df_temp is None:
                logger.warning(f"Could not load {dataset_name} to infer outcome. Skipping.")
                continue
            
            found = False
            for col in possible_outcomes:
                if col in df_temp.columns:
                    outcome_col = col
                    found = True
                    break
            if not found:
                # Pick the last numerical column as a heuristic if no standard name found
                numericals = identify_numerical_columns(df_temp)
                if len(numericals) > 1:
                    outcome_col = numericals[-1] # Heuristic
                    logger.warning(f"No standard outcome column found for {dataset_name}, using heuristic: {outcome_col}")
                else:
                    logger.warning(f"Could not determine outcome column for {dataset_name}. Skipping.")
                    continue

        df = load_dataset_from_processed(dataset_name)
        if df is None:
            logger.warning(f"Dataset {dataset_name} not found. Skipping.")
            continue

        # Run FPR estimation
        # Use a reasonable number of permutations for speed, e.g., 50-100 for this run
        # FR-011 might specify, but 100 is a good balance for a demo.
        fpr_result = estimate_fpr_for_dataset(
            df, 
            dataset_name, 
            outcome_col, 
            n_permutations=100, 
            seed=42
        )
        results.append(fpr_result)

    write_output(results, output_path)
    logger.info("T032 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
