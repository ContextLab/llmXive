"""
Baseline simulation runner for evaluating statistical significance with non-independent observations.

This script runs a Monte Carlo simulation to estimate the Type I error rate of a naive
independent-samples t-test under varying levels of intra-cluster correlation (ICC).
It serves as a violation baseline (ignoring cluster structure) to demonstrate the inflation
of false positives when cluster-aware inference is not used.

Usage:
    python code/run_simulation_baseline.py --icc 0.1 --iterations 1000 --seed 42
"""
import argparse
import sys
import os
import pandas as pd
from config import load_config, set_seed, validate_config, ICC_RANGE, ICC_STEP, DEFAULT_SEED
from simulation_runner import run_baseline_simulation


def parse_args():
    """Parse command-line arguments for the baseline simulation."""
    parser = argparse.ArgumentParser(
        description="Run baseline simulation to evaluate naive t-test Type I error rates."
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
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=ICC_STEP,
        help=f"Step size for ICC if running a range (default: {ICC_STEP})."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/baseline_results.csv",
        help="Path to the output CSV file (default: data/derived/baseline_results.csv)."
    )
    return parser.parse_args()


def main():
    """Execute the baseline simulation and write results to CSV."""
    args = parse_args()

    # Validate output directory
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load and validate configuration
    cfg = load_config()
    cfg["icc"] = args.icc
    cfg["n_iterations"] = args.iterations
    cfg["seed"] = args.seed
    
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Set random seed
    set_seed(cfg["seed"])

    print(f"Starting baseline simulation: ICC={args.icc}, Iterations={args.iterations}, Seed={args.seed}")

    # Run simulation
    results = run_baseline_simulation(
        icc=args.icc,
        n_iterations=args.iterations,
        seed=args.seed
    )

    if not results:
        print("Simulation returned no results.", file=sys.stderr)
        sys.exit(1)

    # Convert to DataFrame and write to CSV
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False)
    
    print(f"Results written to {args.output}")
    print(f"Total rows: {len(df)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())