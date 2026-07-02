"""
Script to run the robust simulation for evaluating statistical significance
in A/B tests with non-independent observations.

This script implements the full simulation pipeline including:
- Data generation with varying intra-cluster correlation (ICC)
- Cluster-robust t-test
- Block permutation test
- Aggregation of results with Clopper-Pearson confidence intervals

Output is written to data/derived/robustResults.csv
"""
import argparse
import sys
import os

import pandas as pd

from config import load_config, set_seed, validate_config, ICC_RANGE, ICC_STEP, DEFAULT_SEED
from simulation_runner import run_robust_simulation
from analysis import aggregate_errors


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run robust simulation for A/B test significance with clustered data."
    )
    parser.add_argument(
        "--icc",
        type=float,
        default=None,
        help="Specific ICC value to test. If not provided, uses --icc-range and --icc-step."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs=2,
        metavar=("START", "END"),
        default=None,
        help="Range of ICC values to test [start, end]. Default: [0.0, 0.5]."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC values. Default: 0.1."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of simulation iterations per ICC value. Default: 1000."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility. Default: 42."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/robustResults.csv",
        help="Output file path. Default: data/derived/robustResults.csv"
    )
    return parser.parse_args()


def main():
    """Main entry point for the robust simulation script."""
    args = parse_args()

    # Load base configuration
    cfg = load_config()
    cfg["seed"] = args.seed
    cfg["n_iterations"] = args.iterations

    # Set random seed
    set_seed(cfg["seed"])

    # Determine ICC values to test
    if args.icc is not None:
        icc_values = [args.icc]
    else:
        start = args.icc_range[0] if args.icc_range else ICC_RANGE[0]
        end = args.icc_range[1] if args.icc_range else ICC_RANGE[-1]
        step = args.icc_step if args.icc_step is not None else ICC_STEP
        icc_values = [round(start + i * step, 2) for i in range(int((end - start) / step) + 1)]

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Running robust simulation with {len(icc_values)} ICC values and {args.iterations} iterations each.")
    print(f"ICC values: {icc_values}")

    # Run simulation for each ICC value
    all_results = []
    for icc in icc_values:
        print(f"  Processing ICC = {icc}...")
        cfg["icc"] = icc
        results = run_robust_simulation(cfg)
        all_results.extend(results)

    # Convert to DataFrame
    df = pd.DataFrame(all_results)

    # Aggregate results to compute error rates and confidence intervals
    alpha_levels = [0.01, 0.05, 0.10]  # Default alpha levels
    if "alpha_levels" in cfg:
        alpha_levels = cfg["alpha_levels"]

    aggregated = aggregate_errors(df, alpha_levels)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write results to CSV
    aggregated.to_csv(args.output, index=False)
    print(f"Results written to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())