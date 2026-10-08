"""
Script to merge baseline and robust simulation results into a final report.

Reads data/derived/baseline_results.csv and data/derived/robustResults.csv,
aggregates by ICC and Alpha, computes error rates and Clopper-Pearson CIs,
and writes data/derived/final_report.csv.
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from scipy.stats import beta

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import parse_cli_args, load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_results(baseline_path: str, robust_path: str) -> tuple:
    """Load baseline and robust results from CSV files."""
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_path}")
    if not os.path.exists(robust_path):
        raise FileNotFoundError(f"Robust results file not found: {robust_path}")

    baseline_df = pd.read_csv(baseline_path)
    robust_df = pd.read_csv(robust_path)

    logger.info(f"Loaded baseline results: {len(baseline_df)} rows")
    logger.info(f"Loaded robust results: {len(robust_df)} rows")

    if len(baseline_df) == 0:
        raise ValueError(f"Baseline results file is empty: {baseline_path}")
    if len(robust_df) == 0:
        raise ValueError(f"Robust results file is empty: {robust_path}")

    return baseline_df, robust_df

def prepare_baseline_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare baseline results for aggregation."""
    # Ensure required columns exist
    required_cols = ['icc', 'alpha', 'rejected']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in baseline results")

    # Rename columns to match expected schema
    df = df.rename(columns={
        'icc': 'ICC',
        'alpha': 'Alpha',
        'rejected': 'rejected'
    })

    # Add method column
    df['Method'] = 'Naive'

    return df

def prepare_robust_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare robust results for aggregation."""
    # Ensure required columns exist
    required_cols = ['icc', 'alpha', 'method', 'rejected']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in robust results")

    # Rename columns to match expected schema
    df = df.rename(columns={
        'icc': 'ICC',
        'alpha': 'Alpha',
        'method': 'Method',
        'rejected': 'rejected'
    })

    return df

def compute_error_rates_and_ci(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute empirical error rates and Clopper-Pearson confidence intervals.
    
    Aggregates by ICC, Alpha, and Method.
    """
    # Group by ICC, Alpha, Method
    grouped = df.groupby(['ICC', 'Alpha', 'Method'], as_index=False)
    
    results = []
    for (icc, alpha, method), group in grouped:
        n = len(group)
        rejections = group['rejected'].sum()
        
        # Empirical error rate
        error_rate = rejections / n if n > 0 else 0.0
        
        # Clopper-Pearson confidence interval (exact method)
        # Using scipy.stats.beta for the interval
        if n > 0:
            ci_lower = beta.ppf(0.025, rejections, n - rejections + 1) if rejections > 0 else 0.0
            ci_upper = beta.ppf(0.975, rejections + 1, n - rejections) if rejections < n else 1.0
        else:
            ci_lower = 0.0
            ci_upper = 0.0
        
        results.append({
            'ICC': icc,
            'Alpha': alpha,
            'Method': method,
            'Empirical_Error_Rate': error_rate,
            'CI_Lower': ci_lower,
            'CI_Upper': ci_upper
        })
    
    return pd.DataFrame(results)

def main():
    """Main entry point for merging results."""
    parser = argparse.ArgumentParser(
        description='Merge baseline and robust simulation results into a final report.'
    )
    parser.add_argument('--baseline-path', type=str, 
                      default='data/derived/baseline_results.csv',
                      help='Path to baseline results CSV')
    parser.add_argument('--robust-path', type=str,
                      default='data/derived/robustResults.csv',
                      help='Path to robust results CSV')
    parser.add_argument('--output-path', type=str,
                      default='data/derived/final_report.csv',
                      help='Path for output final report CSV')
    
    args, unknown = parser.parse_known_args()
    
    # Load config and parse CLI args (for consistency with other scripts)
    cfg = load_config()
    cfg = parse_cli_args(unknown, cfg)
    
    logger.info(f"Starting merge process...")
    logger.info(f"Baseline path: {args.baseline_path}")
    logger.info(f"Robust path: {args.robust_path}")
    logger.info(f"Output path: {args.output_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    try:
        # Load results
        baseline_df, robust_df = load_results(args.baseline_path, args.robust_path)
        
        # Prepare for aggregation
        baseline_prepared = prepare_baseline_for_aggregation(baseline_df)
        robust_prepared = prepare_robust_for_aggregation(robust_df)
        
        # Combine dataframes
        combined_df = pd.concat([baseline_prepared, robust_prepared], ignore_index=True)
        logger.info(f"Combined dataframe has {len(combined_df)} rows")
        
        # Compute error rates and CIs
        final_report = compute_error_rates_and_ci(combined_df)
        
        # Verify output schema
        expected_columns = {'ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper'}
        actual_columns = set(final_report.columns)
        
        if expected_columns != actual_columns:
            missing = expected_columns - actual_columns
            extra = actual_columns - expected_columns
            error_msg = f"Schema mismatch. Missing: {missing}, Extra: {extra}"
            raise ValueError(error_msg)
        
        if len(final_report) == 0:
            raise ValueError("Final report is empty after aggregation")
        
        # Write output
        final_report.to_csv(args.output_path, index=False)
        logger.info(f"Successfully wrote final report to: {args.output_path}")
        logger.info(f"Report contains {len(final_report)} rows")
        
        # Print summary
        logger.info("Summary of final report:")
        for method in final_report['Method'].unique():
            method_rows = final_report[final_report['Method'] == method]
            avg_error = method_rows['Empirical_Error_Rate'].mean()
            logger.info(f"  {method}: Average error rate = {avg_error:.4f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during merge process: {str(e)}")
        raise

if __name__ == '__main__':
    sys.exit(main())
