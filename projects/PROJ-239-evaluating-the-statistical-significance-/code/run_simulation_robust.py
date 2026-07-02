"""
Script to run the robust simulation for evaluating statistical significance
of A/B test results with non-independent observations.

This script performs simulations across a range of Intra-Class Correlation (ICC)
values, applying cluster-robust methods (Cluster-Robust t-test and Block Permutation)
to estimate empirical Type I error rates.

Usage:
    python code/run_simulation_robust.py --icc 0.1 --iterations 1000 --seed 42
    python code/run_simulation_robust.py --icc-range 0.0 0.5 --icc-step 0.1 --iterations 1000
"""
import argparse
import sys
import os
import numpy as np
import pandas as pd
from code.config import load_config, set_seed, validate_config
from code.simulation_runner import run_robust_simulation
from code.analysis import aggregate_errors
from code.config import ALPHA_LEVELS


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run robust simulation for A/B test significance with non-independent observations."
    )
    parser.add_argument(
        "--icc",
        type=float,
        default=None,
        help="Specific ICC value to test. If provided, overrides --icc-range and --icc-step."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs=2,
        metavar=("START", "END"),
        default=None,
        help="Range of ICC values [start, end] to test. Requires --icc-step."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC range. Used with --icc-range."
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
        "--output",
        type=str,
        default="data/derived/robustResults.csv",
        help="Path to output CSV file (default: data/derived/robustResults.csv)."
    )
    parser.add_argument(
        "--alpha-list",
        type=float,
        nargs="+",
        default=None,
        help="List of alpha levels to test (e.g., --alpha-list 0.01 0.05 0.10). Overrides default."
    )
    return parser.parse_args()


def main():
    """Main entry point for the robust simulation script."""
    args = parse_args()

    # Build configuration
    cfg = load_config()
    cfg["n_iterations"] = args.iterations
    cfg["seed"] = args.seed

    # Handle ICC configuration
    if args.icc is not None:
        cfg["icc_range"] = [args.icc]
    elif args.icc_range is not None and args.icc_step is not None:
        start, end = args.icc_range
        step = args.icc_step
        cfg["icc_range"] = []
        current = start
        while current <= end + 1e-9:  # Floating point tolerance
            cfg["icc_range"].append(round(current, 2))
            current += step
    else:
        # Default behavior if no ICC args provided
        cfg["icc_range"] = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    # Handle alpha levels
    if args.alpha_list is not None:
        cfg["alpha_levels"] = sorted(args.alpha_list)
    else:
        cfg["alpha_levels"] = ALPHA_LEVELS

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Set seed
    set_seed(cfg["seed"])

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    print(f"Starting robust simulation with ICC range: {cfg['icc_range']}")
    print(f"Alpha levels: {cfg['alpha_levels']}")
    print(f"Iterations per ICC: {cfg['n_iterations']}")
    print(f"Seed: {cfg['seed']}")

    all_results = []
    for icc in cfg["icc_range"]:
        print(f"Running simulation for ICC = {icc}...")
        cfg["icc"] = icc
        set_seed(cfg["seed"] + int(icc * 1000))  # Different seed per ICC for variety

        # Run robust simulation
        results = run_robust_simulation(cfg)
        all_results.extend(results)

    # Convert results to DataFrame
    df_results = pd.DataFrame(all_results)

    # Aggregate errors
    df_aggregated = aggregate_errors(
        df_results.to_dict("records"),
        cfg["alpha_levels"]
    )

    # Save raw results
    df_results.to_csv(args.output, index=False)
    print(f"Raw results saved to {args.output}")

    # Save aggregated results
    aggregated_path = args.output.replace(".csv", "_aggregated.csv")
    df_aggregated.to_csv(aggregated_path, index=False)
    print(f"Aggregated results saved to {aggregated_path}")

    print("Simulation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())