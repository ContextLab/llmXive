import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from scipy import stats
from analysis import run_t_test, run_linear_regression
from utils import pin_random_seed
from config import Config, get_config

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str = "data/processed") -> pd.DataFrame:
    """Load a dataset from the processed directory."""
    # Try common naming conventions
    possible_paths = [
        os.path.join(processed_dir, f"{dataset_name}.csv"),
        os.path.join(processed_dir, dataset_name),
        os.path.join(processed_dir, f"{dataset_name}_cleaned.csv"),
        os.path.join(processed_dir, f"{dataset_name}_baseline.csv")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return pd.read_csv(path)
    
    # If not found, try to find any CSV that matches the dataset name pattern
    import glob
    pattern = os.path.join(processed_dir, f"*{dataset_name}*.csv")
    matches = glob.glob(pattern)
    if matches:
        return pd.read_csv(matches[0])
    
    raise FileNotFoundError(f"Could not find dataset: {dataset_name}")

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable while keeping predictors fixed.
    This creates a dataset where there is no true relationship between predictors and outcome.
    """
    pin_random_seed(seed)
    null_df = df.copy()
    
    # Shuffle the outcome column
    outcome_values = null_df[outcome_col].values.copy()
    np.random.shuffle(outcome_values)
    null_df[outcome_col] = outcome_values
    
    return null_df

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    outcome_col: str, 
    predictor_cols: List[str],
    n_permutations: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate (FPR) for a dataset by running permutation tests.
    
    The FPR is the proportion of tests where p-value <= alpha when the null hypothesis
    is true (i.e., when we shuffle the outcome).
    """
    pin_random_seed(seed)
    
    significant_count = 0
    p_values = []
    
    logger.info(f"Running {n_permutations} permutation tests for FPR estimation...")
    
    for i in range(n_permutations):
        # Generate null dataset
        null_df = generate_null_dataset(df, outcome_col, seed=seed + i)
        
        # Run statistical tests on null data
        test_results = {}
        
        # T-test for each predictor vs outcome
        for col in predictor_cols:
            try:
                t_result = run_t_test(null_df, col, outcome_col)
                if t_result and 'p_value' in t_result:
                    p_val = t_result['p_value']
                    p_values.append(p_val)
                    if p_val <= alpha:
                        significant_count += 1
            except Exception as e:
                logger.debug(f"Skipping t-test for {col}: {e}")
        
        # Linear regression for each predictor
        for col in predictor_cols:
            try:
                reg_result = run_linear_regression(null_df, col, outcome_col)
                if reg_result and 'p_value' in reg_result:
                    p_val = reg_result['p_value']
                    p_values.append(p_val)
                    if p_val <= alpha:
                        significant_count += 1
            except Exception as e:
                logger.debug(f"Skipping regression for {col}: {e}")
    
    total_tests = len(p_values)
    fpr = significant_count / total_tests if total_tests > 0 else 0.0
    
    return {
        "dataset_name": df.name if hasattr(df, 'name') else "unknown",
        "n_permutations": n_permutations,
        "total_tests": total_tests,
        "significant_tests": significant_count,
        "fpr": fpr,
        "alpha": alpha,
        "p_values_sample": p_values[:10] if len(p_values) > 0 else []
    }

def write_output(results: List[Dict[str, Any]], output_path: str = "data/processed/null_fpr_metrics.json"):
    """Write FPR metrics to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "description": "False Positive Rate estimation via permutation testing",
        "alpha_threshold": 0.05,
        "datasets_analyzed": len(results),
        "results": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Written FPR metrics to {output_path}")
    return output_path

def main():
    """Main entry point for T032: Permutation Null FPR estimation."""
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config = get_config()
    
    # Load baseline metrics to identify datasets
    try:
        baseline_metrics = load_baseline_metrics()
        logger.info(f"Loaded baseline metrics with {len(baseline_metrics.get('datasets', []))} datasets")
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed without baseline metrics: {e}")
        logger.error("Please run baseline analysis (T012) first.")
        return 1
    
    # Identify outcome and predictor columns from baseline metrics or config
    outcome_col = config.get("OUTCOME_COLUMN", "target") if hasattr(config, 'get') else "target"
    if not hasattr(config, 'get'):
        outcome_col = "target"
    
    # If outcome column not specified in config, try to infer from data
    if outcome_col == "target" and baseline_metrics.get('datasets'):
        first_dataset = baseline_metrics['datasets'][0]
        # Try to find common outcome column names
        possible_outcomes = ['target', 'outcome', 'y', 'label', 'class']
        for col in possible_outcomes:
            if col in first_dataset.get('columns', []):
                outcome_col = col
                break
    
    logger.info(f"Using outcome column: {outcome_col}")
    
    results = []
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed") if hasattr(config, 'get') else "data/processed"
    
    # Process each dataset from baseline metrics
    for dataset_entry in baseline_metrics.get('datasets', []):
        dataset_name = dataset_entry.get('dataset_name') or dataset_entry.get('name')
        if not dataset_name:
            logger.warning(f"Skipping dataset entry without name: {dataset_entry}")
            continue
        
        logger.info(f"Processing dataset: {dataset_name}")
        
        try:
            # Load the dataset
            df = load_dataset_from_processed(dataset_name, processed_dir)
            
            # Identify predictor columns (exclude outcome and non-numeric)
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if outcome_col in numeric_cols:
                numeric_cols.remove(outcome_col)
            
            predictor_cols = numeric_cols
            
            if len(predictor_cols) == 0:
                logger.warning(f"No predictor columns found for {dataset_name}, skipping")
                continue
            
            # Estimate FPR
            fpr_result = estimate_fpr_for_dataset(
                df, 
                outcome_col, 
                predictor_cols,
                n_permutations=1000,
                alpha=0.05,
                seed=42
            )
            
            results.append(fpr_result)
            logger.info(f"FPR for {dataset_name}: {fpr_result['fpr']:.4f}")
            
        except FileNotFoundError as e:
            logger.warning(f"Could not load dataset {dataset_name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing {dataset_name}: {e}")
            continue
    
    # Write output
    if results:
        output_path = write_output(results)
        logger.info(f"Successfully wrote FPR metrics for {len(results)} datasets")
        
        # Print summary
        avg_fpr = np.mean([r['fpr'] for r in results])
        logger.info(f"Average FPR across datasets: {avg_fpr:.4f}")
        
        if avg_fpr > 0.10:
            logger.warning(f"High average FPR ({avg_fpr:.4f}) detected. This may indicate issues with the statistical tests or data.")
        
        return 0
    else:
        logger.error("No datasets were successfully processed. No output written.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
