"""
Task T032: Implement permutation null dataset generation for FPR estimation.

Generates null datasets by shuffling the outcome variable while keeping predictors fixed.
Runs statistical tests on these null datasets to estimate the False Positive Rate (FPR).
Outputs metrics to data/processed/null_fpr_metrics.json.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing utilities
from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_t_test, run_linear_regression

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str) -> pd.DataFrame:
    """Load a cleaned dataset from data/processed/."""
    # Try common naming patterns
    paths = [
        f"data/processed/{dataset_name}.csv",
        f"data/processed/{dataset_name}_cleaned.csv",
        f"data/processed/baseline_{dataset_name}.csv"
    ]
    for path in paths:
        if os.path.exists(path):
            return pd.read_csv(path)
    raise FileNotFoundError(f"Could not find dataset: {dataset_name} in data/processed/")

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable.
    
    Args:
        df: Original dataframe
        outcome_col: Name of the outcome/target column
        rng: Random number generator for reproducibility
        
    Returns:
        DataFrame with shuffled outcome column
    """
    null_df = df.copy()
    null_df[outcome_col] = rng.permutation(null_df[outcome_col].values)
    return null_df

def estimate_fpr_for_dataset(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_cols: List[str],
    n_permutations: int = 100,
    alpha: float = 0.05,
    rng: np.random.Generator = None
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate for a dataset using permutation testing.
    
    Runs statistical tests on permuted datasets and calculates the proportion
    of tests that incorrectly reject the null hypothesis (p <= alpha).
    
    Args:
        df: Original dataframe
        outcome_col: Name of the outcome column
        predictor_cols: List of predictor column names
        n_permutations: Number of permutations to run
        alpha: Significance threshold
        rng: Random number generator
        
    Returns:
        Dictionary with FPR metrics
    """
    if rng is None:
        rng = np.random.default_rng()
    
    significant_count = 0
    p_values = []
    
    logger.info(f"Running {n_permutations} permutations for FPR estimation...")
    
    for i in range(n_permutations):
        # Generate null dataset
        null_df = generate_null_dataset(df, outcome_col, rng)
        
        # Run t-test for each predictor
        test_p_values = []
        for pred_col in predictor_cols:
            if pred_col not in null_df.columns or null_df[pred_col].dtype not in [np.int64, np.float64]:
                continue
            
            try:
                # Run t-test
                result = run_t_test(null_df, outcome_col, pred_col)
                if result and 'p_value' in result:
                    p_val = result['p_value']
                    test_p_values.append(p_val)
                    if p_val <= alpha:
                        significant_count += 1
            except Exception as e:
                logger.debug(f"T-test failed for {pred_col}: {e}")
                continue
        
        p_values.extend(test_p_values)
    
    # Calculate FPR
    total_tests = len(p_values)
    fpr = significant_count / total_tests if total_tests > 0 else 0.0
    
    return {
        "n_permutations": n_permutations,
        "total_tests": total_tests,
        "significant_tests": significant_count,
        "fpr": round(fpr, 4),
        "mean_p_value": round(float(np.mean(p_values)), 4) if p_values else None,
        "median_p_value": round(float(np.median(p_values)), 4) if p_values else None,
        "alpha": alpha
    }

def main():
    """Main entry point for T032."""
    setup_logging("INFO")
    config = get_config()
    
    # Pin random seed for reproducibility
    seed = config.get("RANDOM_SEED", 42)
    pin_random_seed(seed)
    rng = np.random.default_rng(seed)
    
    logger.info(f"Starting T032: Permutation Null FPR Estimation (seed={seed})")
    
    # Load baseline metrics to get dataset info
    try:
        baseline_metrics = load_baseline_metrics()
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed without baseline metrics: {e}")
        return 1
    
    if not baseline_metrics or 'datasets' not in baseline_metrics:
        logger.error("Baseline metrics missing 'datasets' key")
        return 1
    
    results = []
    n_permutations = config.get("BOOTSTRAP_ITERATIONS", 100)  # Reduced for FPR estimation
    alpha = 0.05
    
    for dataset_info in baseline_metrics.get('datasets', []):
        dataset_name = dataset_info.get('name')
        outcome_col = dataset_info.get('outcome_column')
        predictor_cols = dataset_info.get('predictor_columns', [])
        
        if not dataset_name or not outcome_col:
            logger.warning(f"Skipping dataset {dataset_name}: missing metadata")
            continue
        
        try:
            logger.info(f"Processing dataset: {dataset_name}")
            df = load_dataset_from_processed(dataset_name)
            
            # Estimate FPR
            fpr_metrics = estimate_fpr_for_dataset(
                df=df,
                outcome_col=outcome_col,
                predictor_cols=predictor_cols,
                n_permutations=n_permutations,
                alpha=alpha,
                rng=rng
            )
            
            fpr_metrics['dataset_name'] = dataset_name
            fpr_metrics['outcome_column'] = outcome_col
            fpr_metrics['n_predictors'] = len(predictor_cols)
            
            results.append(fpr_metrics)
            logger.info(f"FPR for {dataset_name}: {fpr_metrics['fpr']:.4f}")
            
        except FileNotFoundError as e:
            logger.warning(f"Dataset {dataset_name} not found: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing {dataset_name}: {e}")
            continue
    
    # Compile final output
    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "seed": seed,
        "n_permutations": n_permutations,
        "alpha": alpha,
        "summary": {
            "total_datasets_processed": len(results),
            "overall_fpr": round(np.mean([r['fpr'] for r in results]), 4) if results else 0.0,
            "fpr_std": round(float(np.std([r['fpr'] for r in results])), 4) if results else 0.0
        },
        "datasets": results
    }
    
    # Write output
    output_path = "data/processed/null_fpr_metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Successfully wrote FPR metrics to {output_path}")
    return 0

def write_output(results: List[Dict[str, Any]], output_path: str = "data/processed/null_fpr_metrics.json"):
    """Helper function to write results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    sys.exit(main())
