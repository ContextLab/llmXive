"""
Aggregation module for T029c: Data Aggregation.

Aggregates simulation results from individual run outputs into a single
summary CSV file with the required schema.
"""
import os
import json
import glob
import hashlib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from .entities import CausalEstimate
from .metrics import calculate_bias_metrics

RESULTS_DIR = "data/results"
RUN_OUTPUT_PATTERN = os.path.join(RESULTS_DIR, "run_*.json")
SUMMARY_OUTPUT = os.path.join(RESULTS_DIR, "simulation_summary.csv")

def load_run_results(run_file: str) -> Optional[Dict[str, Any]]:
    """Load a single run result file."""
    try:
        with open(run_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {run_file}: {e}")
        return None

def compute_run_id(seed: int, beta: float) -> str:
    """Compute deterministic run ID as SHA-256 hash of 'seed_beta'."""
    hash_input = f"{seed}_{beta}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def calculate_coverage_rate(estimates: List[CausalEstimate], ground_truth: float) -> float:
    """
    Calculate coverage rate: proportion of CIs containing ground_truth.
    
    Args:
        estimates: List of CausalEstimate objects with CI bounds
        ground_truth: The true ATE value
    
    Returns:
        Coverage rate as a float between 0 and 1
    """
    if not estimates:
        return 0.0
    
    contained_count = 0
    for est in estimates:
        # CausalEstimate should have lower_ci and upper_ci
        lower = est.lower_ci
        upper = est.upper_ci
        if lower is not None and upper is not None:
            if lower <= ground_truth <= upper:
                contained_count += 1
    
    return contained_count / len(estimates)

def aggregate_results() -> pd.DataFrame:
    """
    Aggregate all run results into a single DataFrame.
    
    Reads all run_*.json files from data/results, extracts estimates,
    calculates bias, RMSE, and coverage rates, and returns a DataFrame
    with the required schema.
    
    Schema: [beta, method, estimator, ate, bias, rmse, coverage_rate, 
             seed, run_id, ground_truth_ate, beta_value, status]
    """
    # Find all run result files
    run_files = sorted(glob.glob(RUN_OUTPUT_PATTERN))
    
    if not run_files:
        raise FileNotFoundError(
            f"No run result files found matching pattern: {RUN_OUTPUT_PATTERN}"
        )
    
    all_records = []
    
    for run_file in run_files:
        run_data = load_run_results(run_file)
        if run_data is None:
            continue
        
        # Extract metadata
        seed = run_data.get('seed')
        beta = run_data.get('beta')
        ground_truth_ate = run_data.get('ground_truth_ate')
        alpha = run_data.get('alpha')
        status = run_data.get('status', 'completed')
        
        if seed is None or beta is None or ground_truth_ate is None:
            print(f"Warning: Missing metadata in {run_file}, skipping")
            continue
        
        run_id = compute_run_id(seed, beta)
        
        # Process each method/estimator combination
        results = run_data.get('results', {})
        
        for method, method_results in results.items():
            for estimator, est_data in method_results.items():
                ate = est_data.get('ate')
                se = est_data.get('se')
                lower_ci = est_data.get('lower_ci')
                upper_ci = est_data.get('upper_ci')
                
                if ate is None:
                    continue
                
                # Calculate bias and RMSE
                bias = abs(ate - ground_truth_ate)
                rmse = np.sqrt((ate - ground_truth_ate) ** 2)
                
                # Create CausalEstimate object for coverage calculation
                est_obj = CausalEstimate(
                  ate=ate,
                  se=se,
                  lower_ci=lower_ci,
                  upper_ci=upper_ci,
                  method=method,
                  estimator=estimator,
                  seed=seed
                )
                
                # Coverage rate is calculated per (method, estimator, beta)
                # For this single run, it's either 0 or 1
                coverage_rate = 1.0 if (lower_ci is not None and upper_ci is not None and 
                                        lower_ci <= ground_truth_ate <= upper_ci) else 0.0
                
                record = {
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
                    'beta_value': beta,  # Explicitly include beta_value
                    'status': status
                }
                
                all_records.append(record)
    
    if not all_records:
        raise ValueError("No valid records found in any run result files")
    
    df = pd.DataFrame(all_records)
    
    # Ensure correct column order
    expected_columns = [
        'beta', 'method', 'estimator', 'ate', 'bias', 'rmse', 
        'coverage_rate', 'seed', 'run_id', 'ground_truth_ate', 
        'beta_value', 'status'
    ]
    
    # Reorder columns if they exist
    existing_cols = [col for col in expected_columns if col in df.columns]
    df = df[existing_cols]
    
    return df

def save_summary_dataframe(df: pd.DataFrame, output_path: str = SUMMARY_OUTPUT) -> str:
    """
    Save the aggregated DataFrame to CSV.
    
    Args:
        df: DataFrame with aggregated results
        output_path: Path to save the CSV file
    
    Returns:
        Path to the saved file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Saved aggregated results to {output_path}")
    print(f"Total records: {len(df)}")
    print(f"Unique betas: {df['beta'].unique().tolist()}")
    print(f"Unique methods: {df['method'].unique().tolist()}")
    print(f"Unique estimators: {df['estimator'].unique().tolist()}")
    
    return output_path

def main():
    """Main entry point for aggregation script."""
    print("Starting data aggregation...")
    
    try:
        df = aggregate_results()
        output_path = save_summary_dataframe(df)
        print(f"Aggregation complete. Output: {output_path}")
    except Exception as e:
        print(f"Aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()
