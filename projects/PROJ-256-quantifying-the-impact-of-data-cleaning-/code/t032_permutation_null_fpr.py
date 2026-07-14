import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import run_t_test, load_datasets_from_raw, identify_numerical_columns, identify_categorical_columns, run_linear_regression

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str = "data/processed") -> pd.DataFrame:
    """Load a specific dataset from the processed directory."""
    # Handle both raw and cleaned dataset naming conventions
    possible_paths = [
        os.path.join(processed_dir, f"{dataset_name}.csv"),
        os.path.join(processed_dir, f"{dataset_name}_cleaned.csv"),
        os.path.join(processed_dir, f"{dataset_name}_outlier_removed.csv"),
        os.path.join(processed_dir, f"{dataset_name}_imputed.csv")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Loading dataset from: {path}")
            return pd.read_csv(path)
    
    # Fallback: try to find in raw data if processed not found
    raw_dir = "data/raw"
    possible_raw_paths = [
        os.path.join(raw_dir, f"{dataset_name}.csv"),
        os.path.join(raw_dir, dataset_name)
    ]
    
    for path in possible_raw_paths:
        if os.path.exists(path):
            logger.info(f"Loading dataset from raw: {path}")
            if os.path.isdir(path):
                # Try to find CSV in directory
                csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
                if csv_files:
                    return pd.read_csv(os.path.join(path, csv_files[0]))
            else:
                return pd.read_csv(path)
    
    raise FileNotFoundError(f"Could not find dataset: {dataset_name}")

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable while keeping predictors fixed.
    This breaks any true relationship between predictors and outcome.
    """
    if seed is not None:
        pin_random_seed(seed)
    
    null_df = df.copy()
    null_df[outcome_col] = null_df[outcome_col].sample(frac=1, random_state=seed if seed else np.random.randint(0, 2**32)).values
    logger.info(f"Generated null dataset by shuffling outcome column '{outcome_col}'")
    return null_df

def estimate_fpr_for_dataset(
    df: pd.DataFrame, 
    outcome_col: str, 
    predictor_cols: List[str],
    alpha: float = 0.05,
    n_permutations: int = 100,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate (FPR) for a dataset by running statistical tests
    on permuted (null) datasets.
    
    FPR = proportion of tests where p <= alpha when null hypothesis is true.
    """
    if seed is not None:
        pin_random_seed(seed)
    
    results = {
        'dataset_name': df.attrs.get('name', 'unknown'),
        'outcome_column': outcome_col,
        'n_permutations': n_permutations,
        'alpha': alpha,
        't_test_fpr': 0.0,
        't_test_significant_count': 0,
        'regression_fpr': 0.0,
        'regression_significant_count': 0,
        'details': []
    }
    
    significant_t_tests = 0
    significant_regressions = 0
    
    for i in range(n_permutations):
        perm_seed = seed + i if seed else None
        null_df = generate_null_dataset(df, outcome_col, seed=perm_seed)
        
        # Run t-test
        t_test_p = None
        try:
            # Try to run t-test on numerical predictors vs outcome
            for pred in predictor_cols:
                if pred in null_df.columns and pd.api.types.is_numeric_dtype(null_df[pred]):
                    # Simple t-test: compare outcome across binary split of predictor
                    # Or if outcome is binary, compare predictor means
                    if pd.api.types.is_numeric_dtype(null_df[outcome_col]):
                        # Continuous outcome: need a grouping variable
                        # For simplicity, use median split of first numerical predictor
                        if pred != outcome_col:
                            median_val = null_df[pred].median()
                            group_a = null_df[null_df[pred] <= median_val][outcome_col]
                            group_b = null_df[null_df[pred] > median_val][outcome_col]
                            
                            if len(group_a) > 1 and len(group_b) > 1:
                                t_stat, p_val = run_t_test(group_a, group_b)
                                if p_val is not None and p_val <= alpha:
                                    significant_t_tests += 1
                                    break
                    else:
                        # Binary outcome: compare predictor means between groups
                        if pred != outcome_col:
                            group_0 = null_df[null_df[outcome_col] == 0][pred]
                            group_1 = null_df[null_df[outcome_col] == 1][pred]
                            
                            if len(group_0) > 1 and len(group_1) > 1:
                                t_stat, p_val = run_t_test(group_0, group_1)
                                if p_val is not None and p_val <= alpha:
                                    significant_t_tests += 1
                                    break
        except Exception as e:
            logger.debug(f"T-test failed for permutation {i}: {e}")
        
        # Run linear regression
        reg_sig = False
        try:
            # Simple linear regression: outcome ~ first numerical predictor
            for pred in predictor_cols:
                if pred in null_df.columns and pred != outcome_col and pd.api.types.is_numeric_dtype(null_df[pred]):
                    if pd.api.types.is_numeric_dtype(null_df[outcome_col]):
                        try:
                            reg_result = run_linear_regression(null_df, outcome_col, [pred])
                            if reg_result and 'p_values' in reg_result:
                                p_val = reg_result['p_values'][0]
                                if p_val <= alpha:
                                    reg_sig = True
                                    significant_regressions += 1
                                    break
                        except:
                            pass
                    break
        except Exception as e:
            logger.debug(f"Regression failed for permutation {i}: {e}")
        
        results['details'].append({
            'permutation': i,
            't_test_significant': significant_t_tests > len(results['details']),
            'regression_significant': reg_sig
        })
    
    # Calculate FPR
    results['t_test_significant_count'] = significant_t_tests
    results['t_test_fpr'] = significant_t_tests / n_permutations if n_permutations > 0 else 0.0
    
    results['regression_significant_count'] = significant_regressions
    results['regression_fpr'] = significant_regressions / n_permutations if n_permutations > 0 else 0.0
    
    logger.info(
        f"FPR estimation for {results['dataset_name']}: "
        f"T-test FPR={results['t_test_fpr']:.3f}, "
        f"Regression FPR={results['regression_fpr']:.3f}"
    )
    
    return results

def write_output(results: List[Dict[str, Any]], output_path: str):
    """Write FPR metrics to JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    final_report = {
        'generated_at': datetime.now().isoformat(),
        'methodology': 'Permutation null dataset generation (outcome shuffled)',
        'alpha_threshold': 0.05,
        'datasets_analyzed': len(results),
        'results': results,
        'summary': {
            'mean_t_test_fpr': np.mean([r['t_test_fpr'] for r in results]) if results else 0.0,
            'mean_regression_fpr': np.mean([r['regression_fpr'] for r in results]) if results else 0.0,
            'total_datasets': len(results)
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Wrote FPR metrics to {output_path}")

def main():
    """Main entry point for T032: Permutation Null FPR Estimation."""
    logger.info("Starting T032: Permutation Null FPR Estimation")
    
    # Configuration
    baseline_metrics_path = "data/processed/baseline_metrics.json"
    processed_dir = "data/processed"
    output_path = "data/processed/null_fpr_metrics.json"
    n_permutations = 100  # Reduced for speed in testing; can be increased for production
    seed = 42
    
    # Load baseline metrics to get dataset list
    try:
        baseline_metrics = load_baseline_metrics(baseline_metrics_path)
        logger.info(f"Loaded baseline metrics with {len(baseline_metrics.get('datasets', []))} datasets")
    except FileNotFoundError:
        logger.error(f"Baseline metrics not found at {baseline_metrics_path}. Cannot proceed without baseline data.")
        sys.exit(1)
    
    datasets = baseline_metrics.get('datasets', [])
    if not datasets:
        logger.warning("No datasets found in baseline metrics. Nothing to analyze.")
        # Write empty report
        write_output([], output_path)
        return
    
    all_results = []
    
    for dataset_entry in datasets:
        dataset_name = dataset_entry.get('dataset_name') or dataset_entry.get('name')
        outcome_col = dataset_entry.get('outcome_column')
        
        if not dataset_name:
            logger.warning(f"Skipping entry without dataset_name: {dataset_entry}")
            continue
        
        if not outcome_col:
            logger.warning(f"Skipping {dataset_name}: no outcome_column defined")
            continue
        
        try:
            # Load dataset
            df = load_dataset_from_processed(dataset_name, processed_dir)
            
            # Identify numerical columns for predictors
            numerical_cols = identify_numerical_columns(df)
            predictor_cols = [c for c in numerical_cols if c != outcome_col]
            
            if not predictor_cols:
                logger.warning(f"No predictor columns found for {dataset_name}")
                continue
            
            # Estimate FPR
            result = estimate_fpr_for_dataset(
                df=df,
                outcome_col=outcome_col,
                predictor_cols=predictor_cols,
                n_permutations=n_permutations,
                seed=seed
            )
            all_results.append(result)
            
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset_name}: {e}")
            continue
    
    # Write output
    write_output(all_results, output_path)
    
    logger.info("T032 completed successfully")

if __name__ == "__main__":
    main()
