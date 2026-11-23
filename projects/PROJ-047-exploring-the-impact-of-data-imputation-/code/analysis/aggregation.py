"""
Aggregation module for combining simulation results.
Handles the aggregation of multiple runs into summary statistics.
"""
import os
import json
import glob
import hashlib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def compute_run_id(seed: int, beta: float) -> str:
    """
    Compute a unique run ID based on seed and beta.
    
    Args:
        seed: Random seed for the run
        beta: MNAR parameter beta
    
    Returns:
        SHA-256 hash of the string "{seed}_{beta}"
    """
    input_str = f"{seed}_{beta}"
    return hashlib.sha256(input_str.encode()).hexdigest()

def load_run_results(results_dir: str = "data/results") -> List[Dict[str, Any]]:
    """
    Load all run result files from the results directory.
    
    Args:
        results_dir: Directory containing run result JSON files
    
    Returns:
        List of dictionaries containing run results
    """
    runs = []
    pattern = os.path.join(results_dir, "run_*.json")
    
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r') as f:
                run_data = json.load(f)
                runs.append(run_data)
        except Exception as e:
            logger.warning(f"Failed to load {filepath}: {e}")
    
    return runs

def calculate_coverage_rate(estimates: List[Dict[str, Any]], ground_truth_ate: float) -> float:
    """
    Calculate the coverage rate of confidence intervals.
    
    Args:
        estimates: List of estimate dictionaries with 'ci_lower' and 'ci_upper'
        ground_truth_ate: The true ATE value
    
    Returns:
        Proportion of CIs that contain the ground truth ATE
    """
    if not estimates:
        return np.nan
    
    covered = 0
    total = 0
    
    for est in estimates:
        if est.get('status') == 'success' and not np.isnan(est.get('ci_lower', np.nan)):
            ci_lower = est['ci_lower']
            ci_upper = est['ci_upper']
            
            if ci_lower <= ground_truth_ate <= ci_upper:
                covered += 1
            total += 1
    
    if total == 0:
        return np.nan
    
    return covered / total

def aggregate_results(runs_list: List[Dict]) -> pd.DataFrame:
    """
    Aggregate a list of run dictionaries into a single DataFrame.
    
    Args:
        runs_list: List of dictionaries, each representing a simulation run
    
    Returns:
        DataFrame with columns: [beta, method, estimator, ate, bias, rmse, 
        coverage_rate, seed, run_id, ground_truth_ate, status, vif, 
        mnar_correlation, mnar_p_value]
    """
    all_rows = []
    
    for run in runs_list:
        run_id = run.get('run_id')
        seed = run.get('seed')
        beta = run.get('beta')
        ground_truth_ate = run.get('ground_truth_ate')
        vif = run.get('vif', np.nan)
        mnar_correlation = run.get('mnar_correlation', np.nan)
        mnar_p_value = run.get('mnar_p_value', np.nan)
        
        # Process each result in the run
        results = run.get('results', [])
        
        for res in results:
            method = res.get('method')
            estimator = res.get('estimator')
            status = res.get('status', 'unknown')
            ate = res.get('ate', np.nan)
            se = res.get('se', np.nan)
            ci_lower = res.get('ci_lower', np.nan)
            ci_upper = res.get('ci_upper', np.nan)
            
            # Calculate bias and RMSE
            if status == 'success' and not np.isnan(ate) and not np.isnan(ground_truth_ate):
                bias = abs(ate - ground_truth_ate)
                rmse = abs(ate - ground_truth_ate)  # Simplified for single estimate
            else:
                bias = np.nan
                rmse = np.nan
            
            # Calculate coverage rate (per run, per method/estimator would be ideal but we use run level)
            # For simplicity, we'll calculate coverage at the run level and repeat for each method/estimator
            # In a more sophisticated version, we'd group by method/estimator
            coverage_rate = np.nan
            if status == 'success' and not np.isnan(ci_lower) and not np.isnan(ci_upper) and not np.isnan(ground_truth_ate):
                if ci_lower <= ground_truth_ate <= ci_upper:
                    coverage_rate = 1.0
                else:
                    coverage_rate = 0.0
            
            row = {
                'beta': beta,
                'method': method,
                'estimator': estimator,
                'ate': ate,
                'bias': bias,
                'rmse': rmse,
                'coverage_rate': coverage_rate,
                'seed': seed,
                'run_id': run_id,
                'ground_truth_ate': ground_truth_ate,
                'status': status,
                'vif': vif,
                'mnar_correlation': mnar_correlation,
                'mnar_p_value': mnar_p_value,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'se': se,
                'error': res.get('error')
            }
            
            all_rows.append(row)
    
    df = pd.DataFrame(all_rows)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['beta', 'ate', 'bias', 'rmse', 'coverage_rate', 'vif', 
                   'mnar_correlation', 'mnar_p_value', 'ci_lower', 'ci_upper', 'se']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def save_summary_dataframe(df: pd.DataFrame, output_path: str = "data/results/simulation_summary.csv"):
    """
    Save the aggregated results DataFrame to a CSV file.
    
    Args:
        df: DataFrame containing aggregated results
        output_path: Path to save the CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved summary to {output_path} with {len(df)} rows")

def main():
    """
    CLI entry point for testing aggregation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Aggregate simulation results')
    parser.add_argument('--input-dir', type=str, default='data/results', help='Directory with run results')
    parser.add_argument('--output', type=str, default='data/results/simulation_summary.csv', help='Output CSV path')
    
    args = parser.parse_args()
    
    # Load runs
    runs = load_run_results(args.input_dir)
    
    if not runs:
        logger.warning("No run results found. Creating empty DataFrame.")
        df = pd.DataFrame()
    else:
        # Aggregate
        df = aggregate_results(runs)
    
    # Save
    save_summary_dataframe(df, args.output)
    
    print(f"Aggregation complete. Output: {args.output}")
    if not df.empty:
        print(f"Summary statistics:\n{df.describe()}")

if __name__ == '__main__':
    main()
