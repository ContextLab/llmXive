"""
Script to generate the final aggregated report from simulation results.

This script reads the baseline and robust simulation results, aggregates
the error rates using the Clopper-Pearson method, and writes the final
report to data/derived/final_report.csv.

The report contains columns: ICC, Alpha, Method, Empirical_Error_Rate, CI_Lower, CI_Upper.
"""
import os
import sys
import argparse
import pandas as pd

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import load_config, ALPHA_LEVELS, ICC_RANGE
from analysis import aggregate_errors
from simulation_runner import run_baseline_simulation, run_robust_simulation
from data_generator import generate_data
from estimators import run_naive_ttest_with_warning, run_cluster_robust_ttest, run_block_permutation

def run_full_aggregation(n_iterations=1000, seed=42):
    """
    Run simulations for all ICC levels and aggregate results into the final report.
    
    Args:
        n_iterations: Number of simulation iterations per ICC level
        seed: Random seed for reproducibility
        
    Returns:
        pd.DataFrame: Final report with error rates and confidence intervals
    """
    config = load_config()
    all_results = []
    
    # Run baseline simulation for all ICC levels
    print("Running baseline simulations...")
    for icc in ICC_RANGE:
        print(f"  ICC = {icc}")
        results = run_baseline_simulation(icc, n_iterations, seed)
        all_results.extend(results)
        
    # Run robust simulations for all ICC levels
    print("Running robust simulations...")
    for icc in ICC_RANGE:
        print(f"  ICC = {icc}")
        results = run_robust_simulation(icc, n_iterations, seed)
        all_results.extend(results)
        
    # Aggregate errors
    print("Aggregating results...")
    df = aggregate_errors(all_results, ALPHA_LEVELS)
    
    # Rename columns to match final report specification
    df_final = df.rename(columns={
        'icc': 'ICC',
        'alpha': 'Alpha',
        'method': 'Method',
        'error_rate': 'Empirical_Error_Rate',
        'ci_lower': 'CI_Lower',
        'ci_upper': 'CI_Upper'
    })
    
    # Reorder columns
    df_final = df_final[['ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper']]
    
    return df_final

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Generate final report from simulation results')
    parser.add_argument('--iterations', type=int, default=1000, 
                      help='Number of simulation iterations per ICC level')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default='data/derived/final_report.csv',
                      help='Output file path')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Run aggregation
    df_final = run_full_aggregation(n_iterations=args.iterations, seed=args.seed)
    
    # Write to CSV
    df_final.to_csv(args.output, index=False)
    print(f"Final report written to {args.output}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())