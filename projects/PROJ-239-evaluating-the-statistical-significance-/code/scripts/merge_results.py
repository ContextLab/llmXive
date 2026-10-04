"""
Merge baseline and robust simulation results into a final report.

This script reads the raw simulation outputs, aggregates them by ICC and Alpha,
computes empirical error rates and Clopper-Pearson confidence intervals,
and writes the final report to data/derived/final_report.csv.
"""
import os
import sys
import argparse
import logging

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import load_config, parse_cli_args, set_seed
from code.analysis import aggregate_errors, select_ci_method
from scipy.stats import beta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_results(baseline_path: str, robust_path: str) -> tuple:
    """Load baseline and robust result DataFrames."""
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_path}")
    if not os.path.exists(robust_path):
        raise FileNotFoundError(f"Robust results file not found: {robust_path}")

    df_baseline = pd.read_csv(baseline_path)
    df_robust = pd.read_csv(robust_path)

    logger.info(f"Loaded baseline results: {len(df_baseline)} rows")
    logger.info(f"Loaded robust results: {len(df_robust)} rows")

    return df_baseline, df_robust

def prepare_baseline_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare baseline results for aggregation.
    Expected schema: iteration, icc, p_value, rejected
    """
    if 'icc' not in df.columns:
        raise ValueError("Baseline results missing 'icc' column")
    if 'p_value' not in df.columns:
        raise ValueError("Baseline results missing 'p_value' column")
    if 'rejected' not in df.columns:
        # If rejected column doesn't exist, compute it from p_value and a default alpha
        # However, we need alpha levels to compute rejection. We'll handle this in aggregation.
        logger.warning("Baseline results missing 'rejected' column. Will compute during aggregation.")

    return df.copy()

def prepare_robust_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare robust results for aggregation.
    Expected schema: iteration, icc, method, p_value, rejected
    """
    if 'icc' not in df.columns:
        raise ValueError("Robust results missing 'icc' column")
    if 'method' not in df.columns:
        raise ValueError("Robust results missing 'method' column")
    if 'p_value' not in df.columns:
        raise ValueError("Robust results missing 'p_value' column")
    if 'rejected' not in df.columns:
        logger.warning("Robust results missing 'rejected' column. Will compute during aggregation.")

    return df.copy()

def compute_error_rates_and_ci(df: pd.DataFrame, alpha_levels: list) -> pd.DataFrame:
    """
    Compute empirical error rates and Clopper-Pearson confidence intervals.

    Args:
        df: DataFrame with 'icc', 'method', 'p_value', and optionally 'rejected'
        alpha_levels: List of alpha levels to evaluate

    Returns:
        DataFrame with columns: ICC, Alpha, Method, Empirical_Error_Rate, CI_Lower, CI_Upper
    """
    results = []

    # Determine unique ICCs and methods
    iccs = df['icc'].unique()
    methods = df['method'].unique() if 'method' in df.columns else ['baseline']

    for icc in sorted(iccs):
        icc_data = df[df['icc'] == icc]

        for method in methods:
            if 'method' in df.columns:
                method_data = icc_data[icc_data['method'] == method]
            else:
                method_data = icc_data

            for alpha in sorted(alpha_levels):
                # Compute rejected if not present
                if 'rejected' not in method_data.columns:
                    rejected = method_data['p_value'] < alpha
                else:
                    # Ensure rejected is boolean
                    rejected = method_data['rejected'].astype(bool)

                n = len(rejected)
                if n == 0:
                    logger.warning(f"No data for ICC={icc}, Method={method}, Alpha={alpha}")
                    continue

                s = rejected.sum()
                error_rate = s / n

                # Clopper-Pearson confidence interval
                if s == 0:
                    ci_lower = 0.0
                    ci_upper = beta.ppf(1 - alpha/2, 1, n)
                elif s == n:
                    ci_lower = beta.ppf(alpha/2, n, 1)
                    ci_upper = 1.0
                else:
                    ci_lower = beta.ppf(alpha/2, s, n - s + 1)
                    ci_upper = beta.ppf(1 - alpha/2, s + 1, n - s)

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
    parser = argparse.ArgumentParser(description='Merge baseline and robust simulation results.')
    parser.add_argument('--baseline', type=str, default='data/derived/baseline_results.csv',
                      help='Path to baseline results CSV')
    parser.add_argument('--robust', type=str, default='data/derived/robustResults.csv',
                      help='Path to robust results CSV')
    parser.add_argument('--output', type=str, default='data/derived/final_report.csv',
                      help='Path to output final report CSV')
    parser.add_argument('--alpha-list', type=str, default=None,
                      help='Comma-separated alpha levels (e.g., 0.01,0.05,0.10)')

    args = parser.parse_args()

    # Load configuration
    cfg = load_config()
    cfg = parse_cli_args(args, cfg)

    # Determine alpha levels
    if args.alpha_list:
        alpha_levels = [float(x) for x in args.alpha_list.split(',')]
    else:
        alpha_levels = cfg.get('alpha_levels', [0.01, 0.05, 0.10])

    logger.info(f"Using alpha levels: {alpha_levels}")

    # Set seed for reproducibility (though not strictly needed for aggregation)
    set_seed(cfg.get('seed', 42))

    # Load results
    try:
        df_baseline, df_robust = load_results(args.baseline, args.robust)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # Verify input data
    if len(df_baseline) == 0:
        logger.error("Baseline results file is empty")
        sys.exit(1)
    if len(df_robust) == 0:
        logger.error("Robust results file is empty")
        sys.exit(1)

    # Prepare data for aggregation
    df_baseline_prep = prepare_baseline_for_aggregation(df_baseline)
    df_robust_prep = prepare_robust_for_aggregation(df_robust)

    # Add method column to baseline for consistent processing
    df_baseline_prep['method'] = 'baseline'

    # Combine datasets
    df_combined = pd.concat([df_baseline_prep, df_robust_prep], ignore_index=True)
    logger.info(f"Combined dataset has {len(df_combined)} rows")

    # Compute error rates and confidence intervals
    final_report = compute_error_rates_and_ci(df_combined, alpha_levels)

    # Verify output schema
    required_columns = {'ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper'}
    actual_columns = set(final_report.columns)

    if not required_columns.issubset(actual_columns):
        missing = required_columns - actual_columns
        logger.error(f"Output missing required columns: {missing}")
        sys.exit(1)

    if len(final_report) == 0:
        logger.error("Failed to compute any error rates")
        sys.exit(1)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write final report
    final_report.to_csv(args.output, index=False)
    logger.info(f"Final report written to {args.output}")
    logger.info(f"Report contains {len(final_report)} rows")

    # Verification
    df_verify = pd.read_csv(args.output)
    if set(df_verify.columns) != required_columns:
        logger.error(f"Verification failed: columns mismatch")
        sys.exit(1)
    if len(df_verify) == 0:
        logger.error("Verification failed: output is empty")
        sys.exit(1)

    logger.info("Verification passed")
    return 0

if __name__ == '__main__':
    sys.exit(main())