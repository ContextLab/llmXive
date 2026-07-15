"""
Baseline Simulation Runner Script

Executes the baseline (naive t-test) simulation across specified ICC values
and writes results to data/derived/baseline_results.csv.

Usage:
    python code/run_simulation_baseline.py --icc 0.1 --iterations 1000 --seed 42
"""
import argparse
import sys
import os
import numpy as np
import pandas as pd

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.config import load_config, set_seed, validate_config, parse_cli_args
from code.simulation_runner import run_baseline_simulation
from code.analysis import aggregate_errors


def parse_args():
    """Parse command-line arguments for the baseline simulation."""
    parser = argparse.ArgumentParser(
        description="Run baseline simulation for A/B test significance evaluation."
    )
    parser.add_argument(
        "--icc",
        type=float,
        required=False,
        default=None,
        help="Specific ICC value to test. If not provided, uses --icc-range and --icc-step."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs=2,
        metavar=("START", "STOP"),
        default=None,
        help="Range [start, stop] for ICC values. Requires --icc-step."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC iteration. Required with --icc-range."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        required=False,
        default=1000,
        help="Number of simulation iterations per ICC value."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=False,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        default="data/derived/baseline_results.csv",
        help="Output file path for results."
    )
    return parser.parse_args()


def main():
    """Main entry point for the baseline simulation."""
    args = parse_args()

    # Load base config
    cfg = load_config()

    # Override with CLI args if provided
    if args.icc is not None:
        cfg['icc_range'] = [args.icc]
        cfg['icc_step'] = None
    elif args.icc_range is not None and args.icc_step is not None:
        start, stop = args.icc_range
        step = args.icc_step
        cfg['icc_range'] = list(np.arange(start, stop + step/2, step))
    elif args.icc_range is not None or args.icc_step is not None:
        print("Error: --icc-range and --icc-step must be provided together.", file=sys.stderr)
        sys.exit(1)

    cfg['iterations'] = args.iterations
    cfg['seed'] = args.seed

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Set random seed
    set_seed(cfg['seed'])

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Starting baseline simulation with {cfg['iterations']} iterations.")
    print(f"Testing ICC values: {cfg['icc_range']}")

    all_results = []

    for icc in cfg['icc_range']:
        print(f"Running simulation for ICC = {icc}...")
        # Run simulation for this ICC
        results = run_baseline_simulation(
            icc=icc,
            n_iterations=cfg['iterations'],
            seed=cfg['seed'] + int(icc * 1000)  # Unique seed per ICC
        )
        
        # Aggregate results for this ICC
        agg_df = aggregate_errors(
            results_list=results,
            alpha_levels=cfg['alpha_levels']
        )
        
        # Add ICC column to results
        agg_df['icc'] = icc
        all_results.append(agg_df)

    if not all_results:
        print("Warning: No results generated.", file=sys.stderr)
        sys.exit(0)

    # Combine all results
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Reorder columns for clarity
    column_order = ['icc', 'alpha', 'method', 'error_rate', 'ci_lower', 'ci_upper']
    final_df = final_df.reindex(columns=[c for c in column_order if c in final_df.columns] + 
                                [c for c in final_df.columns if c not in column_order])

    # Write to CSV
    final_df.to_csv(args.output, index=False)
    print(f"Results written to {args.output}")
    print(f"Total rows: {len(final_df)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())