"""
Script to merge baseline and robust simulation results into a final report.

This script reads the raw p-value outputs from the baseline and robust simulations,
aggregates them by ICC level and Alpha significance level, computes empirical
Type I error rates, and calculates 95% confidence intervals using the
Clopper-Pearson (Exact) method.

Output: data/derived/final_report.csv
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from scipy.stats import beta

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import aggregate_errors, select_ci_method

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_results(filepath: str) -> pd.DataFrame:
    """
    Load simulation results from a CSV file.

    Args:
        filepath: Path to the CSV file containing simulation results.

    Returns:
        DataFrame with simulation results.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing expected columns.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Validate expected columns based on T014 and T021 schemas
    # Baseline: iteration, icc, p_value, rejected
    # Robust: iteration, icc, method, p_value, rejected
    if df.empty:
        raise ValueError(f"Results file is empty: {filepath}")

    if 'p_value' not in df.columns or 'icc' not in df.columns:
        raise ValueError(f"Missing required columns (p_value, icc) in: {filepath}")

    return df

def prepare_baseline_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare baseline results for aggregation by adding a 'method' column.

    Args:
        df: DataFrame with baseline results.

    Returns:
        DataFrame with 'method' column set to 'naive'.
    """
    df['method'] = 'naive'
    # Ensure 'rejected' is boolean if it's not already
    if df['rejected'].dtype == 'object':
        df['rejected'] = df['rejected'].astype(str).str.lower().isin(['true', '1', 'yes'])
    return df

def prepare_robust_for_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure robust results have a valid 'method' column.

    Args:
        df: DataFrame with robust results.

    Returns:
        DataFrame ready for aggregation.
    """
    # Ensure 'rejected' is boolean if it's not already
    if df['rejected'].dtype == 'object':
        df['rejected'] = df['rejected'].astype(str).str.lower().isin(['true', '1', 'yes'])
    return df

def compute_error_rates_and_ci(results_df: pd.DataFrame, alpha_levels: list) -> pd.DataFrame:
    """
    Compute empirical error rates and 95% CIs for each method, ICC, and Alpha.

    Args:
        results_df: Combined DataFrame with columns: icc, method, rejected, p_value.
        alpha_levels: List of alpha levels to evaluate.

    Returns:
        DataFrame with columns: ICC, Alpha, Method, Empirical_Error_Rate, CI_Lower, CI_Upper.
    """
    results = []

    # Ensure numeric types
    results_df['icc'] = pd.to_numeric(results_df['icc'], errors='coerce')
    results_df['rejected'] = results_df['rejected'].astype(bool)

    for method in results_df['method'].unique():
        method_data = results_df[results_df['method'] == method]

        for icc in method_data['icc'].unique():
            if pd.isna(icc):
                continue

            icc_data = method_data[method_data['icc'] == icc]

            for alpha in alpha_levels:
                # Count rejections and total iterations for this alpha
                # Note: The 'rejected' column is already computed relative to a specific alpha
                # in the simulation runner. However, if the simulation runner used a single
                # alpha, we need to re-evaluate p_values against the requested alpha.
                #
                # Check if 'rejected' column is generic or specific to an alpha.
                # If the simulation runner generated 'rejected' based on a single alpha,
                # we must recompute for all alphas using p_value.
                #
                # Assumption: The simulation runner (T014/T021) might have computed 'rejected'
                # based on a specific alpha. To be safe and support multiple alphas,
                # we recompute rejection based on p_value <= alpha.
                rejected_count = (icc_data['p_value'] <= alpha).sum()
                total_count = len(icc_data)

                if total_count == 0:
                    continue

                error_rate = rejected_count / total_count

                # Compute Clopper-Pearson 95% CI
                # beta.ppf(q, a, b)
                # Lower: beta.ppf(alpha/2, k, n-k+1)
                # Upper: beta.ppf(1 - alpha/2, k+1, n-k)
                k = rejected_count
                n = total_count

                if k == 0:
                    ci_lower = 0.0
                else:
                    ci_lower = beta.ppf(alpha / 2, k, n - k + 1)

                if k == n:
                    ci_upper = 1.0
                else:
                    ci_upper = beta.ppf(1 - alpha / 2, k + 1, n - k)

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
    parser = argparse.ArgumentParser(description="Merge baseline and robust results into a final report.")
    parser.add_argument('--baseline-path', type=str, default='data/derived/baseline_results.csv',
                        help='Path to baseline results CSV')
    parser.add_argument('--robust-path', type=str, default='data/derived/robustResults.csv',
                        help='Path to robust results CSV')
    parser.add_argument('--output-path', type=str, default='data/derived/final_report.csv',
                        help='Path for the final report CSV')
    parser.add_argument('--alpha-list', type=str, default=None,
                        help='Comma-separated list of alpha levels (e.g., 0.01,0.05,0.10)')

    args = parser.parse_args()

    # Determine alpha levels
    if args.alpha_list:
        alpha_levels = [float(x.strip()) for x in args.alpha_list.split(',')]
    else:
        # Default from config.py T004
        alpha_levels = [0.01, 0.05, 0.10]

    logger.info(f"Loading baseline results from {args.baseline_path}")
    try:
        baseline_df = load_results(args.baseline_path)
        baseline_df = prepare_baseline_for_aggregation(baseline_df)
        logger.info(f"Loaded {len(baseline_df)} baseline rows")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load baseline results: {e}")
        sys.exit(1)

    logger.info(f"Loading robust results from {args.robust_path}")
    try:
        robust_df = load_results(args.robust_path)
        robust_df = prepare_robust_for_aggregation(robust_df)
        logger.info(f"Loaded {len(robust_df)} robust rows")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load robust results: {e}")
        sys.exit(1)

    # Combine datasets
    # Ensure both have the same columns for concatenation
    # baseline: iteration, icc, p_value, rejected, method
    # robust: iteration, icc, method, p_value, rejected
    combined_df = pd.concat([baseline_df, robust_df], ignore_index=True)

    logger.info(f"Combined dataset size: {len(combined_df)}")

    # Compute error rates and CIs
    logger.info(f"Computing error rates for alpha levels: {alpha_levels}")
    final_report_df = compute_error_rates_and_ci(combined_df, alpha_levels)

    # Sort for readability
    final_report_df = final_report_df.sort_values(by=['Method', 'ICC', 'Alpha'])

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")

    # Write to CSV
    final_report_df.to_csv(args.output_path, index=False)
    logger.info(f"Final report written to {args.output_path}")
    logger.info(f"Report contains {len(final_report_df)} rows")

    # Print a summary
    print("\nFinal Report Summary:")
    print(final_report_df.to_string(index=False))

if __name__ == '__main__':
    main()
