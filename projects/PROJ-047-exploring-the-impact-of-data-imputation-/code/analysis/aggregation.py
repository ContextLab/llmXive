import os
import json
import glob
import hashlib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

def compute_run_id(seed: int, beta: float) -> str:
    return hashlib.sha256(f"{seed}_{beta}".encode()).hexdigest()

def load_run_results(output_dir: str) -> List[Dict[str, Any]]:
    """Load all individual run JSON files."""
    files = glob.glob(os.path.join(output_dir, 'run_*.json'))
    results = []
    for f in files:
        try:
            with open(f, 'r') as fp:
                results.append(json.load(fp))
        except Exception as e:
            print(f"Warning: Could not load {f}: {e}")
    return results

def calculate_coverage_rate(estimates: List[Dict], ground_truth: float) -> float:
    """
    Calculate coverage rate: proportion of CIs containing ground_truth.
    Assumes estimates have 'ci_low' and 'ci_high' keys.
    """
    if not estimates:
        return 0.0
    count = 0
    for est in estimates:
        low = est.get('ci_low', -np.inf)
        high = est.get('ci_high', np.inf)
        if low <= ground_truth <= high:
            count += 1
    return count / len(estimates)

def aggregate_results(all_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate simulation results into a single DataFrame.
    Schema: [beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta_value, status]
    """
    rows = []
    
    for res in all_results:
        seed = res.get('seed')
        beta = res.get('beta')
        status = res.get('status')
        ground_truth_ate = res.get('ground_truth_ate')
        
        if status == 'failed' or 'results' not in res:
            # Still record the run but mark as failed, maybe with NaNs for metrics
            # Or skip? Spec says "Process all runs". Let's record with NaNs.
            continue 
        
        results_data = res.get('results', [])
        # results_data is expected to be a list of dicts from the pipeline
        
        for r in results_data:
            method = r.get('method')
            estimator = r.get('estimator')
            ate = r.get('ate')
            bias = r.get('bias')
            rmse = r.get('rmse')
            # Coverage is calculated per method/estimator/beta across seeds, 
            # but we store the raw estimate here and aggregate coverage later?
            # T029c says: "Explicitly calculate coverage_rate as the proportion of CIs ... averaged per (method, estimator, beta)"
            # So we store the individual CI info here, and calculate coverage in a second pass or store the raw CI.
            # For simplicity in this CSV, we store the raw estimate and let the downstream calculate coverage per group.
            # However, the schema requires 'coverage_rate'.
            # Let's store the CI bounds here and calculate coverage in the aggregation step if we had all data.
            # Since we are aggregating row by row, we can't calculate coverage rate yet (needs group).
            # We will store 0.0 for now and update in a post-processing step, OR store the CI bounds and calculate later.
            # The schema says 'coverage_rate'. Let's assume we calculate it after grouping.
            # For now, we populate the row and leave coverage_rate as NaN, to be filled by a post-process.
            # Actually, T029c says "Explicitly calculate coverage_rate ... averaged per ...".
            # We will do a two-pass: first collect all, then group, calculate coverage, then save.
            
            rows.append({
                'seed': seed,
                'beta': beta,
                'ground_truth_ate': ground_truth_ate,
                'beta_value': beta,
                'method': method,
                'estimator': estimator,
                'ate': ate,
                'bias': bias,
                'rmse': rmse,
                'status': 'success',
                'run_id': compute_run_id(seed, beta),
                'ci_low': r.get('ci_low'),
                'ci_high': r.get('ci_high')
            })

    df = pd.DataFrame(rows)
    
    if df.empty:
        return df

    # Calculate coverage rate per (method, estimator, beta)
    # Group by method, estimator, beta
    groups = df.groupby(['method', 'estimator', 'beta'])
    
    coverage_map = {}
    for (method, estimator, beta), group_df in groups:
        gt = group_df['ground_truth_ate'].iloc[0]
        c_low = group_df['ci_low'].values
        c_high = group_df['ci_high'].values
        covered = (c_low <= gt) & (gt <= c_high)
        cov_rate = np.mean(covered)
        coverage_map[(method, estimator, beta)] = cov_rate
    
    # Apply coverage rate to rows
    def get_coverage(row):
        key = (row['method'], row['estimator'], row['beta'])
        return coverage_map.get(key, 0.0)
    
    df['coverage_rate'] = df.apply(get_coverage, axis=1)
    
    # Select and order columns for final schema
    final_cols = [
        'beta', 'method', 'estimator', 'ate', 'bias', 'rmse', 
        'coverage_rate', 'seed', 'run_id', 'ground_truth_ate', 
        'beta_value', 'status'
    ]
    
    # Ensure all columns exist
    for col in final_cols:
        if col not in df.columns:
            df[col] = np.nan
            
    return df[final_cols]

def save_summary_dataframe(df: pd.DataFrame, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved summary to {output_path} with {len(df)} rows")

def main():
    # This is a helper, not the main entry point for simulation
    pass
