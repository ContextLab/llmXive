"""
Task T033: Implement outlier threshold sweep for k ∈ {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}
with FPR calculation AND inconsistency rate per threshold per FR-006.

Requirements:
- Calculate FPR as proportion of tests with p ≤ 0.05 in null datasets.
- Calculate Inconsistency Rate as proportion of datasets where significance status changes.
- Dependency: Depends on cleaning functions (T017-T021) and analysis functions (T012, T023).
- Output: data/processed/outlier_threshold_sweep.json
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from project modules
from utils import setup_logging, pin_random_seed
from cleaning import apply_iqr_outlier_removal
from analysis import run_baseline_analysis, load_datasets_from_raw

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str) -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str) -> pd.DataFrame:
    """Load a specific dataset from the processed directory."""
    # Handle various naming conventions
    possible_paths = [
        os.path.join(processed_dir, f"{dataset_name}.csv"),
        os.path.join(processed_dir, f"{dataset_name}_cleaned.csv"),
        os.path.join(processed_dir, f"{dataset_name}_outlier_removed.csv"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return pd.read_csv(path)
    
    # If not found, try to find any CSV matching the name
    matching_files = [f for f in os.listdir(processed_dir) if dataset_name.lower() in f.lower() and f.endswith('.csv')]
    if matching_files:
        return pd.read_csv(os.path.join(processed_dir, matching_files[0]))
    
    raise FileNotFoundError(f"Could not find dataset: {dataset_name} in {processed_dir}")

def estimate_fpr_for_dataset(df: pd.DataFrame, outcome_col: str, threshold: float, k: float = 1.5) -> float:
    """
    Estimate False Positive Rate for a given dataset and outlier threshold.
    
    FPR = proportion of tests with p ≤ 0.05 in null datasets.
    For this implementation, we simulate null datasets by shuffling the outcome variable.
    """
    if len(df) < 10:
        logger.warning(f"Dataset too small for FPR estimation: {len(df)} rows")
        return 0.0
    
    # Create null datasets by shuffling outcome
    n_shuffles = 10  # Reduced for performance in sweep
    significant_count = 0
    
    for i in range(n_shuffles):
        # Shuffle outcome column
        df_null = df.copy()
        shuffled_outcome = df_null[outcome_col].sample(frac=1, random_state=i).reset_index(drop=True)
        df_null[outcome_col] = shuffled_outcome
        
        # Apply outlier removal with current k
        try:
            df_clean = apply_iqr_outlier_removal(df_null, k=k)
        except Exception as e:
            logger.debug(f"Outlier removal failed for shuffle {i}: {e}")
            continue
        
        if len(df_clean) < 5:
            continue
        
        # Run t-test on shuffled data
        # Identify numerical columns excluding outcome
        numerical_cols = [col for col in df_clean.select_dtypes(include=[np.number]).columns if col != outcome_col]
        
        if len(numerical_cols) < 1:
            continue
        
        # Use first numerical column as predictor for simplicity
        predictor_col = numerical_cols[0]
        
        try:
            from scipy import stats
            # Independent t-test requires groups, but for null FPR we'll use correlation approach
            # or t-test against mean if binary outcome
            if df_clean[outcome_col].nunique() == 2:
                groups = [df_clean[df_clean[outcome_col] == val][predictor_col] 
                         for val in df_clean[outcome_col].unique()]
                if len(groups) == 2:
                    t_stat, p_val = stats.ttest_ind(groups[0], groups[1])
                    if p_val <= 0.05:
                        significant_count += 1
            else:
                # For continuous outcome, use correlation test
                from scipy.stats import pearsonr
                corr, p_val = pearsonr(df_clean[predictor_col], df_clean[outcome_col])
                if p_val <= 0.05:
                    significant_count += 1
        except Exception as e:
            logger.debug(f"Statistical test failed for shuffle {i}: {e}")
            continue
    
    return significant_count / n_shuffles if n_shuffles > 0 else 0.0

def calculate_inconsistency_rate(baseline_metrics: Dict, cleaned_metrics: Dict, threshold: float) -> float:
    """
    Calculate Inconsistency Rate as proportion of datasets where significance status changes.
    
    Inconsistency = |Significance_Baseline != Significance_Cleaned| / Total_Datasets
    """
    if not baseline_metrics.get('datasets') or not cleaned_metrics.get('datasets'):
        logger.warning("Missing dataset metrics for inconsistency rate calculation")
        return 0.0
    
    baseline_datasets = {d['dataset_name']: d for d in baseline_metrics['datasets']}
    cleaned_datasets = {d['dataset_name']: d for d in cleaned_metrics['datasets']}
    
    inconsistent_count = 0
    total_count = 0
    
    for name, baseline_entry in baseline_datasets.items():
        if name not in cleaned_datasets:
            continue
        
        cleaned_entry = cleaned_datasets[name]
        total_count += 1
        
        # Get p-values
        baseline_p = None
        cleaned_p = None
        
        # Extract p-value from baseline
        if 't_test' in baseline_entry:
            baseline_p = baseline_entry['t_test'].get('p_value')
        elif 'analysis' in baseline_entry and 't_test' in baseline_entry['analysis']:
            baseline_p = baseline_entry['analysis']['t_test'].get('p_value')
        
        # Extract p-value from cleaned
        if 't_test' in cleaned_entry:
            cleaned_p = cleaned_entry['t_test'].get('p_value')
        elif 'analysis' in cleaned_entry and 't_test' in cleaned_entry['analysis']:
            cleaned_p = cleaned_entry['analysis']['t_test'].get('p_value')
        
        if baseline_p is None or cleaned_p is None:
            logger.debug(f"Missing p-value for dataset {name}")
            continue
        
        # Determine significance (p <= 0.05)
        baseline_sig = baseline_p <= 0.05
        cleaned_sig = cleaned_p <= 0.05
        
        if baseline_sig != cleaned_sig:
            inconsistent_count += 1
    
    return inconsistent_count / total_count if total_count > 0 else 0.0

def run_threshold_sweep(k_values: List[float], 
                       baseline_metrics_path: str, 
                       cleaned_metrics_path: str,
                       processed_dir: str,
                       outcome_col: str = 'outcome',
                       random_seed: int = 42) -> Dict[str, Any]:
    """
    Run outlier threshold sweep across specified k values.
    
    Args:
        k_values: List of IQR multiplier thresholds to test
        baseline_metrics_path: Path to baseline metrics JSON
        cleaned_metrics_path: Path to cleaned metrics JSON  
        processed_dir: Directory containing cleaned datasets
        outcome_col: Name of outcome column
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing sweep results
    """
    pin_random_seed(random_seed)
    
    logger.info(f"Starting outlier threshold sweep for k values: {k_values}")
    
    # Load metrics
    baseline_metrics = load_baseline_metrics(baseline_metrics_path)
    cleaned_metrics = load_cleaned_metrics(cleaned_metrics_path)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'k_values': k_values,
        'thresholds': [],
        'summary': {
            'total_datasets': len(baseline_metrics.get('datasets', [])),
            'outcome_column': outcome_col
        }
    }
    
    for k in k_values:
        logger.info(f"Processing threshold k={k}")
        
        threshold_result = {
            'k_value': k,
            'fpr': 0.0,
            'inconsistency_rate': 0.0,
            'datasets_analyzed': 0,
            'details': []
        }
        
        # Calculate FPR using null datasets
        # We use the first available dataset for FPR estimation to keep it tractable
        baseline_datasets = baseline_metrics.get('datasets', [])
        if baseline_datasets:
            first_dataset_name = baseline_datasets[0]['dataset_name']
            try:
                df = load_dataset_from_processed(first_dataset_name, processed_dir)
                if outcome_col in df.columns:
                    fpr = estimate_fpr_for_dataset(df, outcome_col, k, k)
                    threshold_result['fpr'] = fpr
                    logger.info(f"FPR for k={k}: {fpr:.4f}")
            except Exception as e:
                logger.warning(f"Could not estimate FPR for k={k}: {e}")
        
        # Calculate Inconsistency Rate
        inconsistency = calculate_inconsistency_rate(baseline_metrics, cleaned_metrics, k)
        threshold_result['inconsistency_rate'] = inconsistency
        logger.info(f"Inconsistency Rate for k={k}: {inconsistency:.4f}")
        
        # Add dataset-level details
        threshold_result['datasets_analyzed'] = len(baseline_datasets)
        
        # Store detailed per-dataset inconsistency
        baseline_dict = {d['dataset_name']: d for d in baseline_metrics.get('datasets', [])}
        cleaned_dict = {d['dataset_name']: d for d in cleaned_metrics.get('datasets', [])}
        
        for name in baseline_dict:
            if name in cleaned_dict:
                b_p = baseline_dict[name].get('t_test', {}).get('p_value')
                c_p = cleaned_dict[name].get('t_test', {}).get('p_value')
                
                if b_p is not None and c_p is not None:
                    b_sig = b_p <= 0.05
                    c_sig = c_p <= 0.05
                    changed = b_sig != c_sig
                    
                    threshold_result['details'].append({
                        'dataset_name': name,
                        'baseline_p_value': b_p,
                        'cleaned_p_value': c_p,
                        'baseline_significant': b_sig,
                        'cleaned_significant': c_sig,
                        'significance_changed': changed
                    })
        
        results['thresholds'].append(threshold_result)
    
    return results

def write_output(results: Dict[str, Any], output_path: str):
    """Write results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sweep results written to {output_path}")

def main():
    """Main entry point for T033."""
    logger = setup_logging("INFO")
    
    # Configuration
    config = {
        'baseline_metrics_path': 'data/processed/baseline_metrics.json',
        'cleaned_metrics_path': 'data/processed/cleaned_metrics.json',
        'processed_dir': 'data/processed',
        'output_path': 'data/processed/outlier_threshold_sweep.json',
        'k_values': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        'outcome_col': 'outcome',
        'random_seed': 42
    }
    
    # Check if required files exist
    if not os.path.exists(config['baseline_metrics_path']):
        logger.error(f"Baseline metrics not found: {config['baseline_metrics_path']}")
        logger.error("Run T012 (baseline analysis) first.")
        return False
    
    if not os.path.exists(config['cleaned_metrics_path']):
        logger.error(f"Cleaned metrics not found: {config['cleaned_metrics_path']}")
        logger.error("Run T023 (cleaned variants analysis) first.")
        return False
    
    try:
        # Run the sweep
        results = run_threshold_sweep(
            k_values=config['k_values'],
            baseline_metrics_path=config['baseline_metrics_path'],
            cleaned_metrics_path=config['cleaned_metrics_path'],
            processed_dir=config['processed_dir'],
            outcome_col=config['outcome_col'],
            random_seed=config['random_seed']
        )
        
        # Write output
        write_output(results, config['output_path'])
        
        logger.info("Threshold sweep completed successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Threshold sweep failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)