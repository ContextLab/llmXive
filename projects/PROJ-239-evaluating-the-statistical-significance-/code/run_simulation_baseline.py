"""
Baseline simulation runner for evaluating statistical significance with non-independent observations.

This script runs the naive t-test simulation across specified ICC levels and iterations,
writing results to data/derived/baseline_results.csv.

Usage:
    python code/run_simulation_baseline.py --icc 0.1 --iterations 1000 --seed 42
    python code/run_simulation_baseline.py --icc-range 0.0 0.5 --icc-step 0.1 --iterations 500 --seed 42
"""
import argparse
import sys
import os
import numpy as np
import pandas as pd

# Add project root to path if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.config import load_config, set_seed, validate_config, parse_cli_args
from code.simulation_runner import run_baseline_simulation
from code.analysis import aggregate_errors, select_ci_method

def parse_args():
    """Parse command line arguments for the baseline simulation."""
    parser = argparse.ArgumentParser(
        description="Run baseline simulation for naive t-test under cluster correlation."
    )
    parser.add_argument(
        "--icc",
        type=float,
        default=None,
        help="Specific ICC value to test (e.g., 0.1). Mutually exclusive with --icc-range."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs=2,
        metavar=('START', 'END'),
        default=None,
        help="Range of ICC values to test (start end). Overrides --icc if provided."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=0.1,
        help="Step size for ICC range (default: 0.1). Only used with --icc-range."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of simulation iterations per ICC value (default: 1000)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)."
    )
    parser.add_argument(
        "--alpha-list",
        type=float,
        nargs='+',
        default=None,
        help="List of alpha levels to test (e.g., 0.01 0.05 0.10). Overrides config default."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/baseline_results.csv",
        help="Output file path (default: data/derived/baseline_results.csv)."
    )
    return parser.parse_args()

def main():
    """Execute the baseline simulation and save results."""
    args = parse_args()

    # Build config from CLI args
    cli_cfg = {}
    if args.icc is not None:
        cli_cfg['icc_range'] = [args.icc]
    elif args.icc_range is not None:
        start, end = args.icc_range
        cli_cfg['icc_range'] = np.arange(start, end + args.icc_step / 2, args.icc_step).tolist()
    else:
        # Default range if neither specified
        cli_cfg['icc_range'] = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    if args.alpha_list is not None:
        cli_cfg['alpha_levels'] = args.alpha_list

    # Load base config and update with CLI overrides
    cfg = load_config()
    cfg.update(cli_cfg)
    cfg['n_iterations'] = args.iterations
    cfg['seed'] = args.seed

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Set global seed
    set_seed(cfg['seed'])

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print(f"Running baseline simulation with {len(cfg['icc_range'])} ICC values...")
    print(f"  Iterations: {cfg['n_iterations']}")
    print(f"  Alpha levels: {cfg['alpha_levels']}")
    print(f"  Seed: {cfg['seed']}")

    all_results = []

    for icc in cfg['icc_range']:
        cfg['icc'] = icc
        print(f"  Processing ICC = {icc}...")

        # Run simulation for this ICC
        results = run_baseline_simulation(
            n_clusters=cfg['n_clusters'],
            n_obs_per_cluster=cfg['n_obs_per_cluster'],
            icc=icc,
            n_iterations=cfg['n_iterations'],
            seed=cfg['seed'] + int(icc * 1000)  # Offset seed per ICC for reproducibility
        )

        # Aggregate results
        df_agg = aggregate_errors(results, cfg['alpha_levels'])
        
        # Add ICC column if not present
        if 'icc' not in df_agg.columns:
            df_agg['icc'] = icc

        all_results.append(df_agg)

    # Combine all results
    final_df = pd.concat(all_results, ignore_index=True)

    # Ensure column order: icc, alpha, method, error_rate, ci_lower, ci_upper
    expected_cols = ['icc', 'alpha', 'method', 'error_rate', 'ci_lower', 'ci_upper']
    # Filter to only expected columns if extra exist
    final_df = final_df[[c for c in expected_cols if c in final_df.columns]]

    # Save to CSV
    final_df.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")
    print(f"Total rows: {len(final_df)}")

    return 0

if __name__ == "__main__":
    sys.exit(main())