import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str = "data/processed") -> Optional[pd.DataFrame]:
    """Load a specific dataset from the processed directory."""
    # Look for CSV files matching the dataset name
    pattern = os.path.join(processed_dir, f"{dataset_name}*")
    files = glob.glob(pattern)
    if not files:
        # Try looking in raw directory if not found in processed
        pattern = os.path.join("data/raw", f"{dataset_name}*")
        files = glob.glob(pattern)
    
    if not files:
        logger.warning(f"No dataset found matching pattern: {pattern}")
        return None
    
    # Load the first matching file
    file_path = files[0]
    logger.info(f"Loading dataset from: {file_path}")
    
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            return pd.read_json(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading dataset {file_path}: {e}")
        return None

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable while keeping predictors fixed.
    This breaks any true relationship between predictors and outcome.
    """
    pin_random_seed(seed)
    df_null = df.copy()
    
    # Shuffle the outcome column
    df_null[outcome_col] = df_null[outcome_col].sample(frac=1, random_state=seed).reset_index(drop=True)
    
    logger.info(f"Generated null dataset by shuffling '{outcome_col}' column (seed={seed})")
    return df_null

def estimate_fpr_for_dataset(df_null: pd.DataFrame, dataset_name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Estimate False Positive Rate for a null dataset by running statistical tests.
    FPR is the proportion of tests that yield p <= 0.05 when there should be no relationship.
    """
    if config is None:
        config = get_config()
    
    # Determine outcome column (typically the last column or a specific named column)
    # For this implementation, we assume the last column is the outcome
    outcome_col = df_null.columns[-1]
    predictor_cols = df_null.columns[:-1]
    
    logger.info(f"Estimating FPR for dataset: {dataset_name}, outcome: {outcome_col}")
    
    # Run baseline analysis on the null dataset
    # We need to pass the dataframe directly, not a directory
    result = run_baseline_analysis(
        df=df_null, 
        dataset_name=dataset_name, 
        config=config
    )
    
    if not result or not result.get('success', False):
        logger.warning(f"Baseline analysis failed for null dataset: {dataset_name}")
        return {
            "dataset_name": dataset_name,
            "fpr_estimate": None,
            "p_values": [],
            "significant_tests": 0,
            "total_tests": 0,
            "error": "Baseline analysis failed"
        }
    
    # Extract p-values from the result
    p_values = []
    significant_count = 0
    
    # Look for t-test p-values
    if 't_tests' in result.get('results', {}):
        for test_name, test_data in result['results']['t_tests'].items():
            if 'p_value' in test_data:
                p_val = test_data['p_value']
                p_values.append(p_val)
                if p_val <= 0.05:
                    significant_count += 1
    
    # Look for regression p-values (for coefficients)
    if 'regressions' in result.get('results', {}):
        for model_name, model_data in result['results']['regressions'].items():
            if 'coefficients' in model_data:
                for coef_data in model_data['coefficients']:
                    if 'p_value' in coef_data:
                        p_val = coef_data['p_value']
                        p_values.append(p_val)
                        if p_val <= 0.05:
                            significant_count += 1
    
    total_tests = len(p_values)
    fpr_estimate = significant_count / total_tests if total_tests > 0 else 0.0
    
    logger.info(f"FPR for {dataset_name}: {significant_count}/{total_tests} = {fpr_estimate:.3f}")
    
    return {
        "dataset_name": dataset_name,
        "fpr_estimate": round(fpr_estimate, 4),
        "p_values": [round(p, 4) for p in p_values],
        "significant_tests": significant_count,
        "total_tests": total_tests,
        "outcome_column": outcome_col,
        "num_predictors": len(predictor_cols)
    }
    
    logger.info(f"Running {n_permutations} permutation iterations for {dataset_name}")
    
    for i in range(n_permutations):
        # Generate a new null dataset for each iteration
        pin_random_seed(seed + i)
        df_null_iter = generate_null_dataset(df_null, outcome_col, seed + i)
        
        # Run baseline analysis on the null dataset
        try:
            result = run_baseline_analysis(
                df=df_null_iter,
                dataset_name=f"{dataset_name}_null_iter_{i}",
                config=None
            )
            
            if result and result.get('success'):
                # Count significant t-tests (p <= 0.05)
                if 't_tests' in result:
                    for test_name, test_result in result['t_tests'].items():
                        if 'p_value' in test_result:
                            fpr_results['total_t_tests'] += 1
                            if test_result['p_value'] <= 0.05:
                                fpr_results['significant_t_tests'] += 1
                                fpr_results['t_test_fpr'].append(1.0)
                            else:
                                fpr_results['t_test_fpr'].append(0.0)
                
                # Count significant regressions (p <= 0.05 for any coefficient)
                if 'regressions' in result:
                    for reg_name, reg_result in result['regressions'].items():
                        if 'p_values' in reg_result:
                            has_significant = any(p <= 0.05 for p in reg_result['p_values'] if p is not None)
                            fpr_results['total_regressions'] += 1
                            if has_significant:
                                fpr_results['significant_regressions'] += 1
                                fpr_results['regression_fpr'].append(1.0)
                            else:
                                fpr_results['regression_fpr'].append(0.0)
                            
        except Exception as e:
            logger.warning(f"Error in permutation iteration {i}: {e}")
            continue
    
    # Calculate FPR rates
    if fpr_results['total_t_tests'] > 0:
        fpr_results['t_test_fpr_rate'] = fpr_results['significant_t_tests'] / fpr_results['total_t_tests']
    else:
        fpr_results['t_test_fpr_rate'] = 0.0
        
    if fpr_results['total_regressions'] > 0:
        fpr_results['regression_fpr_rate'] = fpr_results['significant_regressions'] / fpr_results['total_regressions']
    else:
        fpr_results['regression_fpr_rate'] = 0.0
    
    logger.info(f"FPR for {dataset_name}: t-test={fpr_results['t_test_fpr_rate']:.3f}, "
               f"regression={fpr_results['regression_fpr_rate']:.3f}")
    
    return fpr_results

def write_output(results: List[Dict[str, Any]], output_path: str = "data/processed/null_fpr_metrics.json"):
    """Write the FPR estimation results to a JSON file."""
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "description": "False Positive Rate estimation from permutation null datasets",
        "methodology": "Outcome variable shuffled while predictors fixed; FPR = proportion of tests with p <= 0.05",
        "results": results,
        "summary": {
            "total_datasets": len(results),
            "datasets_with_results": sum(1 for r in results if r.get('fpr_estimate') is not None),
            "mean_fpr": np.mean([r['fpr_estimate'] for r in results if r.get('fpr_estimate') is not None]) if any(r.get('fpr_estimate') for r in results) else None,
            "median_fpr": np.median([r['fpr_estimate'] for r in results if r.get('fpr_estimate') is not None]) if any(r.get('fpr_estimate') for r in results) else None
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Null FPR metrics written to: {output_path}")

def main():
    """Main entry point for the permutation null FPR estimation task."""
    # Setup logging
    setup_logging("INFO")
    
    logger.info("Starting permutation null dataset FPR estimation (Task T032)")
    
    # Load configuration
    config = get_config()
    seed = config.get("RANDOM_SEED", 42)
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    # Load configuration
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    random_seed = config.get("RANDOM_SEED", 42)
    n_permutations = config.get("PERMUTATION_ITERATIONS", 10)
    
    if not baseline_metrics:
        logger.error("Could not load baseline metrics. Cannot proceed without dataset list.")
        sys.exit(1)
    
    results = []
    
    # Process each dataset from baseline metrics
    datasets = baseline_metrics.get('datasets', [])
    
    if not datasets:
        logger.warning("No datasets found in baseline metrics.")
        # Try to find datasets in the raw directory
        raw_dir = config.get("RAW_DATA_PATH", "data/raw")
        if os.path.exists(raw_dir):
            for filename in os.listdir(raw_dir):
                if filename.endswith('.csv') or filename.endswith('.json'):
                  dataset_name = os.path.splitext(filename)[0]
                  df = load_dataset_from_processed(dataset_name, raw_dir)
                  if df is not None:
                      # Generate null dataset and estimate FPR
                      null_df = generate_null_dataset(df, df.columns[-1], seed)
                      fpr_result = estimate_fpr_for_dataset(null_df, dataset_name, config)
                      results.append(fpr_result)
                      seed += 1  # Increment seed for next permutation
    else:
        for entry in datasets:
            dataset_name = entry.get('dataset_name') or entry.get('name')
            if not dataset_name:
                logger.warning(f"Skipping entry without dataset name: {entry}")
                continue
            
            logger.info(f"Processing dataset: {dataset_name}")
            
            # Load the dataset
            df = load_dataset_from_processed(dataset_name, processed_dir)
            if df is None:
                # Try raw directory
                df = load_dataset_from_processed(dataset_name, "data/raw")
            
            if df is None:
                logger.error(f"Could not load dataset: {dataset_name}")
                results.append({
                    "dataset_name": dataset_name,
                    "error": "Dataset not found"
                })
                continue
            
            # Generate null dataset by shuffling outcome
            outcome_col = df.columns[-1]  # Assume last column is outcome
            null_df = generate_null_dataset(df, outcome_col, seed)
            
            # Estimate FPR for this null dataset
            fpr_result = estimate_fpr_for_dataset(null_df, dataset_name, config)
            results.append(fpr_result)
            
            seed += 1  # Increment seed for next permutation
    
    # Write output
    output_path = "data/processed/null_fpr_metrics.json"
    write_output(results, output_path)
    
    logger.info("Task T032 completed successfully.")
    return 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
