import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

from utils import setup_logging, pin_random_seed
from analysis import run_t_test, run_linear_regression, load_datasets_from_raw

logger = setup_logging("INFO")

def load_baseline_metrics() -> Dict[str, Any]:
    """Load baseline metrics from the processed directory."""
    path = "data/processed/baseline_metrics.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Baseline metrics not found at {path}. Run baseline analysis first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Load a specific dataset from the processed directory.
    Expects files named like: data/processed/{dataset_name}_raw.csv
    """
    # Try common naming conventions used in the pipeline
    possible_paths = [
        f"data/processed/{dataset_name}_raw.csv",
        f"data/processed/{dataset_name}.csv",
        f"data/raw/{dataset_name}.csv",
        f"data/raw/{dataset_name}_raw.csv"
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            logger.info(f"Loading dataset from {p}")
            return pd.read_csv(p)
    
    logger.warning(f"Could not find raw dataset for {dataset_name} in expected paths.")
    return None

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable while keeping predictors fixed.
    This breaks any true relationship between predictors and outcome.
    """
    pin_random_seed(seed)
    null_df = df.copy()
    
    # Get the outcome column values
    outcome_values = null_df[outcome_col].values
    
    # Shuffle the outcome values
    np.random.shuffle(outcome_values)
    
    # Assign shuffled values back to the dataframe
    null_df[outcome_col] = outcome_values
    
    return null_df

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    outcome_col: str, 
    predictor_cols: List[str],
    n_permutations: int = 100,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate (FPR) for a single dataset by running statistical tests
    on permuted (null) datasets.
    
    FPR is calculated as the proportion of tests where p-value <= alpha (false positives).
    """
    logger.info(f"Estimating FPR for dataset with {len(df)} rows, {n_permutations} permutations")
    
    if len(predictor_cols) == 0:
        logger.warning("No predictor columns found. Skipping FPR estimation.")
        return {"fpr": 0.0, "n_tests": 0, "n_significant": 0, "error": "No predictors"}

    significant_count = 0
    total_tests = 0
    p_values = []

    for i in range(n_permutations):
        seed = i * 1000 + hash(outcome_col) % 10000
        null_df = generate_null_dataset(df, outcome_col, seed)
        
        dataset_significant = False
        
        # Run t-tests for binary outcomes or regression for continuous
        # We'll focus on t-tests as they are common in the baseline analysis
        for col in predictor_cols:
            # Ensure we have enough data for the test
            if null_df[col].nunique() < 2 or null_df[outcome_col].nunique() < 2:
                continue
            
            try:
                # For t-test, we need a binary predictor or we treat it as continuous
                # The baseline analysis typically does t-tests on categorical predictors
                # and regression on continuous. We'll try t-test first if binary, else regression.
                
                if null_df[col].nunique() <= 2:
                    # T-test
                    res = run_t_test(null_df, col, outcome_col)
                    if res and 'p_value' in res:
                        p_val = res['p_value']
                        p_values.append(p_val)
                        total_tests += 1
                        if p_val <= alpha:
                            significant_count += 1
                            dataset_significant = True
                else:
                    # Linear regression
                    res = run_linear_regression(null_df, col, outcome_col)
                    if res and 'p_value' in res:
                        p_val = res['p_value']
                        p_values.append(p_val)
                        total_tests += 1
                        if p_val <= alpha:
                            significant_count += 1
                            dataset_significant = True
            except Exception as e:
                logger.debug(f"Test failed for {col}: {e}")
                continue

    fpr = significant_count / total_tests if total_tests > 0 else 0.0

    return {
        "fpr": fpr,
        "n_tests": total_tests,
        "n_significant": significant_count,
        "mean_p_value": float(np.mean(p_values)) if p_values else None,
        "min_p_value": float(np.min(p_values)) if p_values else None,
        "max_p_value": float(np.max(p_values)) if p_values else None,
        "alpha": alpha
    }

def write_output(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write the FPR metrics to a JSON file."""
    output = {
        "metadata": {
            "generated_at": str(pd.Timestamp.now()),
            "description": "False Positive Rate estimation using permutation null datasets",
            "method": "Shuffled outcome variable while keeping predictors fixed"
        },
        "results": results
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Null FPR metrics written to {output_path}")

def main() -> None:
    """Main entry point for T032: Permutation Null FPR Estimation."""
    logger.info("Starting T032: Permutation Null FPR Estimation")
    
    # Load baseline metrics to get list of datasets and outcome columns
    try:
        baseline_data = load_baseline_metrics()
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Cannot proceed without baseline metrics. Run t012_run_baseline_analysis.py first.")
        sys.exit(1)

    datasets = baseline_data.get("datasets", [])
    if not datasets:
        logger.error("No datasets found in baseline metrics.")
        sys.exit(1)

    results = []
    n_permutations = 100  # Reduced for speed; can be increased for production
    
    for dataset_entry in datasets:
        dataset_name = dataset_entry.get("dataset_name") or dataset_entry.get("name")
        if not dataset_name:
            logger.warning(f"Skipping entry with no name: {dataset_entry}")
            continue

        outcome_col = dataset_entry.get("outcome_column")
        if not outcome_col:
            logger.warning(f"No outcome column defined for {dataset_name}. Skipping.")
            continue

        # Load the raw dataset
        df = load_dataset_from_processed(dataset_name)
        if df is None:
            logger.warning(f"Could not load dataset {dataset_name}. Skipping.")
            continue

        # Identify predictor columns (all numerical columns except outcome)
        # This mirrors the logic in analysis.py roughly
        numerical_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != outcome_col]
        
        if len(numerical_cols) == 0:
            logger.warning(f"No predictor columns found for {dataset_name}. Skipping.")
            continue

        logger.info(f"Running FPR estimation on {dataset_name} with {len(numerical_cols)} predictors")
        
        fpr_result = estimate_fpr_for_dataset(
            df, 
            outcome_col, 
            numerical_cols, 
            n_permutations=n_permutations
        )
        
        fpr_result["dataset_name"] = dataset_name
        fpr_result["n_permutations"] = n_permutations
        fpr_result["n_predictors"] = len(numerical_cols)
        
        results.append(fpr_result)
        logger.info(f"  FPR: {fpr_result['fpr']:.4f} ({fpr_result['n_significant']}/{fpr_result['n_tests']} tests significant)")

    # Write output
    output_path = "data/processed/null_fpr_metrics.json"
    write_output(results, output_path)
    
    logger.info("T032 completed successfully.")

if __name__ == "__main__":
    main()