"""
Baseline Simulation Runner for A/B Test Statistical Significance.

This script executes the baseline simulation (naive t-test) across specified
intra-cluster correlation (ICC) levels to measure Type I error inflation.
It serves as the violation baseline for comparison against cluster-robust methods.

Usage:
    python code/run_simulation_baseline.py --icc 0.1 --iterations 1000 --seed 42
"""
import argparse
import sys
import os

# Ensure the project root is in the path for imports if running from subdirectories
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
import pandas as pd

from code.config import load_config, set_seed, validate_config
from code.simulation_runner import run_baseline_simulation
from code.analysis import aggregate_errors
from code.config import ALPHA_LEVELS


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run baseline simulation for A/B test significance evaluation."
    )
    parser.add_argument(
        "--icc",
        type=float,
        required=True,
        help="Intra-cluster correlation coefficient (e.g., 0.1)."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        required=True,
        help="Number of simulation iterations (e.g., 1000)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Optional step size for ICC range (not used in single-ICC mode)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Validate inputs
    if args.icc < 0.0 or args.icc > 1.0:
        print("Error: ICC must be between 0.0 and 1.0.", file=sys.stderr)
        sys.exit(1)
    if args.iterations < 1:
        print("Error: Iterations must be at least 1.", file=sys.stderr)
        sys.exit(1)

    # Set seed
    set_seed(args.seed)

    # Load base config and override with CLI args
    cfg = load_config()
    cfg['icc'] = args.icc
    cfg['n_iterations'] = args.iterations
    cfg['seed'] = args.seed
    
    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting baseline simulation: ICC={cfg['icc']}, Iterations={cfg['n_iterations']}, Seed={cfg['seed']}")

    # Run simulation
    # run_baseline_simulation returns a list of dicts: [{'iteration': i, 'p_value': p, ...}, ...]
    try:
        results = run_baseline_simulation(
            icc=cfg['icc'],
            n_iterations=cfg['n_iterations'],
            seed=cfg['seed']
        )
    except Exception as e:
        print(f"Simulation execution failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("Warning: Simulation produced no results.", file=sys.stderr)
        sys.exit(1)

    # Convert to DataFrame
    df_results = pd.DataFrame(results)

    # Aggregate errors for the specific ICC and configured alpha levels
    # The aggregate_errors function expects a list of dicts and alpha_levels
    # It returns a DataFrame with error rates and CIs
    summary_df = aggregate_errors(results, ALPHA_LEVELS)

    # Add ICC column to the summary for the output file
    summary_df['icc'] = args.icc

    # Ensure output directory exists
    output_dir = "data/derived"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "baseline_results.csv")

    # Write raw p-values and summary stats to CSV
    # The task requires writing baseline_results.csv. 
    # We will write the summary statistics (error rates) as the primary output,
    # as raw p-values for 1000+ iterations are less useful for the report than the aggregated rates.
    # However, to be safe, we can include both or just the summary. 
    # The spec says "writes data/derived/baseline_results.csv". 
    # Usually, this implies the aggregated results for the report.
    
    # Re-order columns for clarity
    cols = ['icc', 'alpha', 'method', 'error_rate', 'ci_lower', 'ci_upper']
    # Ensure columns exist before reordering
    available_cols = [c for c in cols if c in summary_df.columns]
    if available_cols:
        summary_df = summary_df[available_cols]

    summary_df.to_csv(output_path, index=False)
    print(f"Results written to {output_path}")

    # Exit successfully
    sys.exit(0)


if __name__ == "__main__":
    main()