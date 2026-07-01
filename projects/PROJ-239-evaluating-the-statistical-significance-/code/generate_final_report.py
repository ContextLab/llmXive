"""
Script to generate the final report CSV aggregating simulation results.

This script reads the baseline and robust simulation results, aggregates
them into a unified dataframe, computes empirical Type I error rates and
95% confidence intervals using the Clopper-Pearson method, and writes
the final report to `data/derived/final_report.csv`.

Dependencies:
    - code/simulation_runner.py (run_baseline_simulation, run_robust_simulation)
    - code/analysis.py (aggregate_errors, select_ci_method)
    - code/config.py (load_config, set_seed, validate_config, ALPHA_LEVELS, ICC_RANGE)
"""
import argparse
import os
import sys
import warnings

import numpy as np
import pandas as pd

# Add project root to path if running as script
if os.path.basename(os.path.dirname(__file__)) == 'code':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
else:
    # Assume we are in the root or code dir
    pass

from code.config import load_config, set_seed, validate_config, ALPHA_LEVELS, ICC_RANGE
from code.simulation_runner import run_baseline_simulation, run_robust_simulation
from code.analysis import aggregate_errors, select_ci_method


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate the final aggregated report from simulation results."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs="+",
        default=None,
        help="List of ICC values to simulate (overrides config)."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC range (overrides config)."
    )
    parser.add_argument(
        "--alpha-list",
        type=float,
        nargs="+",
        default=None,
        help="List of alpha levels (overrides config)."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of simulation iterations per ICC."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/final_report.csv",
        help="Output path for the final report CSV."
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=None,
        help="Number of clusters (overrides config)."
    )
    parser.add_argument(
        "--n-obs-per-cluster",
        type=int,
        default=None,
        help="Number of observations per cluster (overrides config)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load base config
    cfg = load_config()

    # Override with CLI args if provided
    if args.icc_range is not None:
        cfg['icc_range'] = args.icc_range
    if args.icc_step is not None:
        cfg['icc_step'] = args.icc_step
    if args.alpha_list is not None:
        cfg['alpha_levels'] = args.alpha_list
    if args.n_clusters is not None:
        cfg['n_clusters'] = args.n_clusters
    if args.n_obs_per_cluster is not None:
        cfg['n_obs_per_cluster'] = args.n_obs_per_cluster

    # Validate config
    validate_config(cfg)
    set_seed(args.seed)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Starting final report generation with {args.iterations} iterations per ICC.")
    print(f"ICC Range: {cfg.get('icc_range', ICC_RANGE)}")
    print(f"Alpha Levels: {cfg.get('alpha_levels', ALPHA_LEVELS)}")

    all_results = []

    # Use the ICC range from config or defaults
    icc_values = cfg.get('icc_range', ICC_RANGE)
    alpha_levels = cfg.get('alpha_levels', ALPHA_LEVELS)
    n_iterations = args.iterations
    n_clusters = cfg.get('n_clusters', 100)
    n_obs_per_cluster = cfg.get('n_obs_per_cluster', 10)
    seed = args.seed

    for icc in icc_values:
        print(f"Running simulations for ICC = {icc}...")
        # Run baseline (naive)
        baseline_results = run_baseline_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed + int(icc * 1000),  # Unique seed per ICC
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster
        )

        # Run robust methods
        robust_results = run_robust_simulation(
            icc=icc,
            n_iterations=n_iterations,
            seed=seed + int(icc * 1000) + 10000,  # Unique seed per ICC
            n_clusters=n_clusters,
            n_obs_per_cluster=n_obs_per_cluster
        )

        # Combine results for this ICC
        # Format: list of dicts with 'method', 'p_value'
        combined = []
        for r in baseline_results:
            combined.append({'method': 'naive_ttest', 'p_value': r['p_value']})
        for r in robust_results:
            # robust_results contains entries for 'cluster_robust' and 'block_permutation'
            combined.append({'method': r['method'], 'p_value': r['p_value']})

        # Aggregate errors for this ICC
        df_agg = aggregate_errors(combined, alpha_levels, n_iterations)
        df_agg['icc'] = icc

        all_results.append(df_agg)

    if not all_results:
        print("No results generated. Check simulation functions.")
        sys.exit(1)

    final_df = pd.concat(all_results, ignore_index=True)

    # Ensure column order and naming matches spec
    # Expected: ICC, Alpha, Method, Empirical_Error_Rate, CI_Lower, CI_Upper
    # aggregate_errors returns: method, icc, alpha, error_rate, ci_lower, ci_upper
    final_df = final_df.rename(columns={
        'icc': 'ICC',
        'alpha': 'Alpha',
        'method': 'Method',
        'error_rate': 'Empirical_Error_Rate',
        'ci_lower': 'CI_Lower',
        'ci_upper': 'CI_Upper'
    })

    # Reorder columns
    final_df = final_df[['ICC', 'Alpha', 'Method', 'Empirical_Error_Rate', 'CI_Lower', 'CI_Upper']]

    # Save to CSV
    final_df.to_csv(args.output, index=False)
    print(f"Final report written to {args.output}")
    print(f"Total rows: {len(final_df)}")

    # Print a sample
    print("\nSample of final report:")
    print(final_df.head(10))


if __name__ == "__main__":
    main()