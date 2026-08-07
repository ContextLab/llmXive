import os
import json
import glob
import hashlib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from .entities import CausalEstimate, SyntheticDataset, ImputationResult

def compute_run_id(seed: int, beta: float) -> str:
    """
    Compute a deterministic run_id as a SHA-256 hash of the string "seed_beta".
    """
    content = f"{seed}_{beta}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def load_run_results(results_dir: str) -> List[Dict[str, Any]]:
    """
    Load all simulation result JSON files from the specified directory.
    Expects files named like 'run_<seed>_<beta>.json' or similar patterns.
    Returns a list of dictionaries containing run data.
    """
    results = []
    pattern = os.path.join(results_dir, "*.json")
    for filepath in glob.glob(pattern):
        # Skip non-run files if necessary, but assume all json in results are run data
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {filepath}: {e}")
    return results

def calculate_coverage_rate(estimates: List[CausalEstimate], ground_truth_ate: float) -> float:
    """
    Calculate the coverage rate: proportion of CIs that contain the ground truth ATE.
    Assumes each CausalEstimate has 'ate', 'se', and potentially 'ci_lower', 'ci_upper'.
    If CI bounds are not directly stored, they are computed as estimate +/- 1.96 * SE.
    """
    if not estimates:
        return 0.0

    contains_truth = 0
    total = len(estimates)

    for est in estimates:
        ci_lower = est.ci_lower if est.ci_lower is not None else est.ate - 1.96 * est.se
        ci_upper = est.ci_upper if est.ci_upper is not None else est.ate + 1.96 * est.se

        if ci_lower <= ground_truth_ate <= ci_upper:
            contains_truth += 1

    return contains_truth / total

def aggregate_results(
    run_results: List[Dict[str, Any]],
    ground_truth_map: Dict[str, float]
) -> pd.DataFrame:
    """
    Aggregate results from multiple runs into a summary DataFrame.
    
    Args:
        run_results: List of dictionaries containing run data (method, estimator, ate, etc.)
        ground_truth_map: Map of run_id -> ground_truth_ate
    
    Returns:
        DataFrame with schema:
        [beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta_value, status]
    """
    rows = []
    
    # Group results by (method, estimator, beta) to calculate coverage rates
    # Structure: {(method, estimator, beta): [list of CausalEstimates]}
    coverage_groups = {}
    
    for run_data in run_results:
        seed = run_data.get('seed')
        beta = run_data.get('beta')
        run_id = compute_run_id(seed, beta)
        ground_truth_ate = ground_truth_map.get(run_id, run_data.get('ground_truth_ate', 0.0))
        
        # Ensure ground_truth_ate is stored for every row (Constitution VI)
        run_data['ground_truth_ate'] = ground_truth_ate
        run_data['beta_value'] = beta
        run_data['run_id'] = run_id
        
        # Process individual estimates within the run
        if 'estimates' in run_data:
            estimates = run_data['estimates']
        else:
            # Fallback: assume flat structure with method, estimator, ate, se, status
            estimates = [run_data]

        for est in estimates:
            method = est.get('method', 'unknown')
            estimator = est.get('estimator', 'unknown')
            ate = est.get('ate', 0.0)
            se = est.get('se', 0.0)
            status = est.get('status', 'success')
            
            # Calculate bias and RMSE
            bias = abs(ate - ground_truth_ate)
            rmse = bias # Simplified RMSE for single estimate; if multiple, use sqrt(mean(bias^2))
            
            # Create a CausalEstimate object for coverage calculation
            ci_lower = est.get('ci_lower')
            ci_upper = est.get('ci_upper')
            causal_est = CausalEstimate(
                method=method,
                estimator=estimator,
                ate=ate,
                se=se,
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                status=status
            )
            
            key = (method, estimator, beta)
            if key not in coverage_groups:
                coverage_groups[key] = []
            coverage_groups[key].append((causal_est, ground_truth_ate))
            
            # Store row data (we will update coverage_rate later)
            rows.append({
                'beta': beta,
                'method': method,
                'estimator': estimator,
                'ate': ate,
                'bias': bias,
                'rmse': rmse,
                'coverage_rate': 0.0, # Placeholder, updated later
                'seed': seed,
                'run_id': run_id,
                'ground_truth_ate': ground_truth_ate,
                'beta_value': beta,
                'status': status
            })

    # Calculate coverage rates per (method, estimator, beta)
    coverage_map = {}
    for key, items in coverage_groups.items():
        method, estimator, beta = key
        est_list = [item[0] for item in items]
        gt = items[0][1] # Ground truth is consistent per run_id, but we take first
        coverage = calculate_coverage_rate(est_list, gt)
        coverage_map[key] = coverage

    # Update rows with correct coverage rates
    for row in rows:
        key = (row['method'], row['estimator'], row['beta'])
        row['coverage_rate'] = coverage_map.get(key, 0.0)

    return pd.DataFrame(rows)

def save_summary_dataframe(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the aggregated results DataFrame to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved summary to {output_path}")

def main():
    """
    Main entry point for data aggregation.
    Loads results, aggregates them, and saves to simulation_summary.csv.
    """
    # Define paths
    results_dir = "data/results"
    output_path = "data/results/simulation_summary.csv"
    
    # Load raw run results (JSON files)
    run_results = load_run_results(results_dir)
    
    if not run_results:
        print("Warning: No run results found to aggregate.")
        # Create an empty DataFrame with the correct schema to satisfy downstream tasks
        df = pd.DataFrame(columns=[
            'beta', 'method', 'estimator', 'ate', 'bias', 'rmse', 
            'coverage_rate', 'seed', 'run_id', 'ground_truth_ate', 'beta_value', 'status'
        ])
        save_summary_dataframe(df, output_path)
        return

    # Reconstruct ground truth map from run data or regenerate if needed
    # Assuming ground_truth_ate is stored in each run_data
    ground_truth_map = {}
    for run_data in run_results:
        seed = run_data.get('seed')
        beta = run_data.get('beta')
        run_id = compute_run_id(seed, beta)
        # Prefer stored value, fallback to 0.5 if missing (should not happen with T029b)
        gt = run_data.get('ground_truth_ate', 0.5)
        ground_truth_map[run_id] = gt

    # Aggregate
    df = aggregate_results(run_results, ground_truth_map)
    
    # Save
    save_summary_dataframe(df, output_path)

if __name__ == "__main__":
    main()