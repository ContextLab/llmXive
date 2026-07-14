"""
T032: Implement permutation null dataset generation for false-positive rate (FPR) estimation.

This script generates null datasets by shuffling the outcome variable while keeping
predictors fixed. It then runs baseline statistical tests on these null datasets
to estimate the false-positive rate (FPR) under the null hypothesis.

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
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis import run_baseline_analysis
from config import Config, get_config
from utils import pin_random_seed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str = "data/processed") -> Optional[pd.DataFrame]:
    """Load a dataset from the processed directory."""
    # Try to find the dataset in processed directory
    # Look for files matching the dataset name
    pattern = f"{dataset_name}*.csv"
    files = list(Path(processed_dir).glob(pattern))
    
    if not files:
        logger.warning(f"No processed dataset found for: {dataset_name}")
        return None
    
    # Use the first matching file
    df = pd.read_csv(files[0])
    logger.info(f"Loaded dataset: {files[0].name} ({len(df)} rows)")
    return df

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, random_seed: int = 42) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable.
    
    This creates a dataset where the null hypothesis is true (no relationship
    between predictors and outcome) by breaking any existing relationship
    through permutation.
    
    Args:
        df: Original dataset
        outcome_col: Name of the outcome variable column
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with shuffled outcome variable
    """
    pin_random_seed(random_seed)
    
    df_null = df.copy()
    
    # Shuffle the outcome variable while keeping predictors fixed
    df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
    
    logger.info(f"Generated null dataset: shuffled {outcome_col} ({len(df_null)} rows)")
    return df_null

def estimate_fpr_for_dataset(
    df_null: pd.DataFrame,
    dataset_name: str,
    outcome_col: str,
    config: Optional[Dict[str, Any]] = None,
    n_permutations: int = 10
) -> Dict[str, Any]:
    """
    Estimate false-positive rate for a dataset using permutation testing.
    
    Args:
        df_null: The null dataset (outcome shuffled)
        dataset_name: Name of the dataset
        outcome_col: Name of the outcome column
        config: Configuration dictionary
        n_permutations: Number of permutation iterations
        
    Returns:
        Dictionary containing FPR estimates for different statistical tests
    """
    if config is None:
        config = {}
    
    seed = config.get("RANDOM_SEED", 42)
    
    fpr_results = {
        "dataset_name": dataset_name,
        "outcome_column": outcome_col,
        "n_permutations": n_permutations,
        "t_test_fpr": [],
        "regression_fpr": [],
        "significant_t_tests": 0,
        "significant_regressions": 0,
        "total_t_tests": 0,
        "total_regressions": 0
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

def write_output(results: List[Dict[str, Any]], output_file: str = "data/processed/null_fpr_metrics.json"):
    """Write FPR metrics to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "description": "False-positive rate estimates from permutation null datasets",
        "fr_011_compliance": "Generated null datasets by shuffling outcomes while keeping predictors fixed",
        "datasets": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Wrote FPR metrics to {output_file}")

def main():
    """Main entry point for T032 permutation null FPR estimation."""
    logger.info("Starting T032: Permutation Null FPR Estimation")
    
    # Load configuration
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    random_seed = config.get("RANDOM_SEED", 42)
    n_permutations = config.get("PERMUTATION_ITERATIONS", 10)
    
    # Load baseline metrics to get dataset information
    baseline_metrics = load_baseline_metrics(os.path.join(processed_dir, "baseline_metrics.json"))
    
    if not baseline_metrics or "datasets" not in baseline_metrics:
        logger.error("No baseline metrics found. Cannot proceed with FPR estimation.")
        sys.exit(1)
    
    all_fpr_results = []
    
    # Process each dataset
    for dataset_entry in baseline_metrics["datasets"]:
        dataset_name = dataset_entry.get("dataset_name")
        
        if not dataset_name:
            logger.warning(f"Skipping entry without dataset_name: {dataset_entry}")
            continue
        
        # Load the dataset
        df = load_dataset_from_processed(dataset_name, processed_dir)
        
        if df is None:
            logger.warning(f"Could not load dataset: {dataset_name}")
            continue
        
        # Identify outcome column (usually the last numerical column or specified in config)
        # For this implementation, we'll try to find a reasonable outcome column
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numerical_cols) < 2:
            logger.warning(f"Dataset {dataset_name} has fewer than 2 numerical columns. Skipping.")
            continue
        
        # Use the last numerical column as outcome (common convention)
        outcome_col = numerical_cols[-1]
        logger.info(f"Using '{outcome_col}' as outcome column for {dataset_name}")
        
        # Estimate FPR for this dataset
        fpr_result = estimate_fpr_for_dataset(
            df_null=df,
            dataset_name=dataset_name,
            outcome_col=outcome_col,
            config={"RANDOM_SEED": random_seed},
            n_permutations=n_permutations
        )
        
        all_fpr_results.append(fpr_result)
    
    # Write output
    output_file = os.path.join(processed_dir, "null_fpr_metrics.json")
    write_output(all_fpr_results, output_file)
    
    logger.info("T032 completed successfully")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
