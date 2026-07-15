"""
Module to generate the final comparison report from simulation results.

This script aggregates results from baseline and robust simulations,
computes empirical Type I error rates with Clopper-Pearson confidence intervals,
and writes the final report to data/derived/final_report.csv.
"""
import argparse
import os
import sys
import warnings
import numpy as np
import pandas as pd
from code.config import load_config, set_seed, validate_config, parse_cli_args
from code.analysis import aggregate_errors, select_ci_method

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate the final statistical significance report."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs="+",
        default=None,
        help="List of ICC values to process (e.g., 0.0 0.1 0.2). Overrides config."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC generation if range not provided."
    )
    parser.add_argument(
        "--alpha-list",
        type=float,
        nargs="+",
        default=None,
        help="List of alpha levels (e.g., 0.01 0.05 0.10). Overrides config."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of simulation iterations (for consistency check)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    return parser.parse_args()

def main():
    """Main entry point for generating the final report."""
    args = parse_args()
    set_seed(args.seed)

    # Load base config and apply CLI overrides
    cfg = load_config()
    if args.icc_range is not None:
        cfg['icc_range'] = args.icc_range
    if args.icc_step is not None:
        cfg['icc_step'] = args.icc_step
    if args.alpha_list is not None:
        cfg['alpha_levels'] = args.alpha_list

    validate_config(cfg)

    # Determine ICC values to process
    if 'icc_range' in cfg and cfg['icc_range'] is not None:
        icc_values = sorted(cfg['icc_range'])
    else:
        # Generate range if not explicitly set
        start = 0.0
        end = cfg.get('icc_max', 0.5)
        step = cfg.get('icc_step', 0.1)
        icc_values = np.arange(start, end + step/2, step).tolist()

    # Ensure output directory exists
    os.makedirs("data/derived", exist_ok=True)

    results = []

    # Load baseline results if available
    baseline_path = "data/derived/baseline_results.csv"
    if os.path.exists(baseline_path):
        try:
            df_baseline = pd.read_csv(baseline_path)
            # Group by ICC and method (usually 'naive')
            # Expected columns: icc, method, p_value (or similar)
            # We need to re-aggregate to match the final report format
            # Assuming the baseline runner stored raw p-values
            if 'p_value' in df_baseline.columns:
                # Group by ICC and method
                grouped = df_baseline.groupby(['icc', 'method'])['p_value'].apply(list).reset_index()
                grouped.columns = ['icc', 'method', 'p_values']
                for _, row in grouped.iterrows():
                    icc = row['icc']
                    method = row['method']
                    p_vals = row['p_values']
                    for alpha in cfg['alpha_levels']:
                        errors = [1 if p < alpha else 0 for p in p_vals]
                        n = len(errors)
                        if n > 0:
                            error_rate = sum(errors) / n
                            ci_method = select_ci_method(error_rate, n)
                            # Use scipy.stats.beta for Clopper-Pearson
                            # Lower bound: beta.ppf(alpha/2, sum+1, n-sum)
                            # Upper bound: beta.ppf(1-alpha/2, sum+1, n-sum)
                            # Note: scipy uses shape parameters a, b
                            # If sum=0, lower=0; if sum=n, upper=1
                            if sum(errors) == 0:
                                ci_lower = 0.0
                            else:
                                ci_lower = beta.ppf(alpha/2, sum(errors), n - sum(errors) + 1)
                            if sum(errors) == n:
                                ci_upper = 1.0
                            else:
                                ci_upper = beta.ppf(1 - alpha/2, sum(errors) + 1, n - sum(errors))
                            
                            results.append({
                                'ICC': icc,
                                'Alpha': alpha,
                                'Method': method,
                                'Empirical_Error_Rate': error_rate,
                                'CI_Lower': ci_lower,
                                'CI_Upper': ci_upper
                            })
        except Exception as e:
            warnings.warn(f"Failed to process baseline results: {e}")
    else:
        warnings.warn(f"Baseline results not found at {baseline_path}. Skipping baseline method.")

    # Load robust results if available
    robust_path = "data/derived/robustResults.csv"
    if os.path.exists(robust_path):
        try:
            df_robust = pd.read_csv(robust_path)
            if 'p_value' in df_robust.columns:
                grouped = df_robust.groupby(['icc', 'method'])['p_value'].apply(list).reset_index()
                grouped.columns = ['icc', 'method', 'p_values']
                for _, row in grouped.iterrows():
                    icc = row['icc']
                    method = row['method']
                    p_vals = row['p_values']
                    for alpha in cfg['alpha_levels']:
                        errors = [1 if p < alpha else 0 for p in p_vals]
                        n = len(errors)
                        if n > 0:
                            error_rate = sum(errors) / n
                            ci_method = select_ci_method(error_rate, n)
                            if sum(errors) == 0:
                                ci_lower = 0.0
                            else:
                                ci_lower = beta.ppf(alpha/2, sum(errors), n - sum(errors) + 1)
                            if sum(errors) == n:
                                ci_upper = 1.0
                            else:
                                ci_upper = beta.ppf(1 - alpha/2, sum(errors) + 1, n - sum(errors))
                            
                            results.append({
                                'ICC': icc,
                                'Alpha': alpha,
                                'Method': method,
                                'Empirical_Error_Rate': error_rate,
                                'CI_Lower': ci_lower,
                                'CI_Upper': ci_upper
                            })
        except Exception as e:
            warnings.warn(f"Failed to process robust results: {e}")
    else:
        warnings.warn(f"Robust results not found at {robust_path}. Skipping robust methods.")

    if not results:
        raise RuntimeError("No simulation results found to generate the final report. "
                           "Please run the baseline and/or robust simulations first.")

    # Create DataFrame and sort
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by=['ICC', 'Alpha', 'Method'])

    # Write to CSV
    output_path = "data/derived/final_report.csv"
    final_df.to_csv(output_path, index=False)
    print(f"Final report written to {output_path}")
    print(f"Total rows: {len(final_df)}")
    print(final_df.head())

    return 0

if __name__ == "__main__":
    sys.exit(main())
