"""Script to merge baseline and robust simulation results into a final report."""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.analysis import aggregate_errors, select_ci_method

def load_results(baseline_path: str, robust_path: str) -> tuple:
    """Load baseline and robust results from CSV files.
    
    Args:
        baseline_path: Path to baseline results CSV.
        robust_path: Path to robust results CSV.
        
    Returns:
        Tuple of (baseline_df, robust_df).
        
    Raises:
        FileNotFoundError: If input files do not exist.
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_path}")
    if not os.path.exists(robust_path):
        raise FileNotFoundError(f"Robust results file not found: {robust_path}")
    
    baseline_df = pd.read_csv(baseline_path)
    robust_df = pd.read_csv(robust_path)
    
    logging.info(f"Loaded baseline results: {len(baseline_df)} rows")
    logging.info(f"Loaded robust results: {len(robust_df)} rows")
    
    return baseline_df, robust_df

def prepare_baseline_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare baseline results for aggregation.
    
    Args:
        df: Baseline results DataFrame.
        
    Returns:
        Prepared DataFrame with 'method' column added.
    """
    df = df.copy()
    df['method'] = 'naive'
    return df

def prepare_robust_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare robust results for aggregation.
    
    Args:
        df: Robust results DataFrame.
        
    Returns:
        Prepared DataFrame.
    """
    return df.copy()

def compute_error_rates_and_ci(
    baseline_df: pd.DataFrame,
    robust_df: pd.DataFrame,
    alpha_levels: list
) -> pd.DataFrame:
    """Compute error rates and confidence intervals for all methods.
    
    Args:
        baseline_df: Baseline results DataFrame.
        robust_df: Robust results DataFrame.
        alpha_levels: List of alpha levels to evaluate.
        
    Returns:
        DataFrame with error rates and confidence intervals.
    """
    # Prepare data
    baseline_df = prepare_baseline_for_aggregation(baseline_df)
    robust_df = prepare_robust_for_aggregation(robust_df)
    
    # Combine all results
    all_results = pd.concat([baseline_df, robust_df], ignore_index=True)
    
    # Aggregate by method, icc, and alpha
    results_list = []
    
    for method in all_results['method'].unique():
        method_df = all_results[all_results['method'] == method]
        
        for icc in method_df['icc'].unique():
            icc_df = method_df[method_df['icc'] == icc]
            
            for alpha in alpha_levels:
                # Calculate empirical error rate
                n = len(icc_df)
                rejections = icc_df['rejected'].sum()
                error_rate = rejections / n if n > 0 else 0.0
                
                # Calculate confidence intervals using Clopper-Pearson
                ci_method = select_ci_method(error_rate, n)
                
                if n > 0:
                    from scipy.stats import beta
                    ci_lower = beta.ppf(alpha / 2, rejections, n - rejections + 1) if rejections > 0 else 0.0
                    ci_upper = beta.ppf(1 - alpha / 2, rejections + 1, n - rejections) if rejections < n else 1.0
                else:
                    ci_lower, ci_upper = 0.0, 1.0
                
                results_list.append({
                    'ICC': icc,
                    'Alpha': alpha,
                    'Method': method,
                    'Empirical_Error_Rate': error_rate,
                    'CI_Lower': ci_lower,
                    'CI_Upper': ci_upper
                })
    
    return pd.DataFrame(results_list)

def main():
    """Main entry point for merging results."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description='Merge simulation results into final report')
    parser.add_argument('--baseline', type=str, default='data/derived/baseline_results.csv',
                        help='Path to baseline results CSV')
    parser.add_argument('--robust', type=str, default='data/derived/robustResults.csv',
                        help='Path to robust results CSV')
    parser.add_argument('--output', type=str, default='data/derived/final_report.csv',
                        help='Path for final report CSV')
    parser.add_argument('--alpha-list', type=str, default='0.01,0.05,0.10',
                        help='Comma-separated alpha levels')
    
    args = parser.parse_args()
    
    # Load results
    baseline_df, robust_df = load_results(args.baseline, args.robust)
    
    # Parse alpha levels
    alpha_levels = [float(x) for x in args.alpha_list.split(',')]
    
    # Compute error rates and CIs
    final_report = compute_error_rates_and_ci(baseline_df, robust_df, alpha_levels)
    
    # Verify output
    required_columns = {'ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper'}
    if set(final_report.columns) != required_columns:
        raise ValueError(f"Output columns mismatch. Expected {required_columns}, got {set(final_report.columns)}")
    
    if len(final_report) == 0:
        raise ValueError("Final report is empty")
    
    # Save output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    final_report.to_csv(args.output, index=False)
    
    logging.info(f"Final report saved to {args.output}")
    logging.info(f"Report contains {len(final_report)} rows")
    
    # Verify content
    print(final_report.head(10))

if __name__ == '__main__':
    main()
