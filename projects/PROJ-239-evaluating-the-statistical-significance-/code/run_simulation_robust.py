"""
Robust Simulation Runner Script.

This script executes the robust A/B test simulation across a range of ICC values
to evaluate the performance of cluster-robust variance and block permutation methods
against the naive baseline.

It reads configuration from `code/config.py`, runs the simulation loop defined in
`code/simulation_runner.py`, aggregates results using `code/analysis.py`, and writes
the final output to `data/derived/robustResults.csv`.
"""

import argparse
import sys
import os
import numpy as np
import pandas as pd

# Ensure project root is in path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.config import load_config, set_seed, validate_config, parse_cli_args
from code.simulation_runner import run_robust_simulation
from code.analysis import aggregate_errors
from code.data_generator import generate_data


def parse_args():
    """Parse command line arguments for the robust simulation."""
    parser = argparse.ArgumentParser(
        description="Run robust simulation for A/B test significance with non-independent observations."
    )
    parser.add_argument(
        "--icc",
        type=float,
        default=None,
        help="Specific ICC value to test. If None, uses range from config."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC range. Overrides config if provided."
    )
    parser.add_argument(
        "--icc-range",
        type=str,
        default=None,
        help="Comma-separated ICC range start,stop. e.g., 0.0,0.5"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of simulation iterations per ICC value."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--alpha-list",
        type=str,
        default=None,
        help="Comma-separated alpha levels. e.g., 0.01,0.05,0.10"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/robustResults.csv",
        help="Path to output CSV file."
    )
    return parser.parse_args()


def main():
    """Main entry point for the robust simulation."""
    args = parse_args()

    # Load base configuration
    cfg = load_config()

    # Override config with CLI arguments
    cli_cfg = parse_cli_args(args)
    cfg.update(cli_cfg)

    # Specific overrides for robust simulation context
    if args.iterations:
        cfg['n_iterations'] = args.iterations
    if args.seed is not None:
        cfg['seed'] = args.seed
    
    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration validation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Set random seed
    set_seed(cfg['seed'])

    print(f"Starting Robust Simulation with seed={cfg['seed']}")
    print(f"ICC Range: {cfg['icc_range']}")
    print(f"Step Size: {cfg['icc_step']}")
    print(f"Iterations: {cfg['n_iterations']}")
    print(f"Alpha Levels: {cfg['alpha_levels']}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Generate ICC values to test
    if args.icc is not None:
        icc_values = [args.icc]
    else:
        start, stop = cfg['icc_range']
        icc_values = np.arange(start, stop + cfg['icc_step'], cfg['icc_step'])
        # Ensure we don't exceed 1.0 due to floating point errors
        icc_values = [ic for ic in icc_values if ic <= 1.0]

    all_results = []

    for icc in icc_values:
        print(f"\n--- Running simulation for ICC = {icc:.2f} ---")
        
        try:
            # Run the robust simulation loop
            # This function internally calls run_robust_simulation which handles
            # the loop, data generation, and running of all three methods
            results = run_robust_simulation(
                icc=icc,
                n_iterations=cfg['n_iterations'],
                seed=cfg['seed'],
                n_clusters=cfg['n_clusters'],
                n_obs_per_cluster=cfg['n_obs_per_cluster']
            )
            
            # Convert results list to DataFrame for aggregation
            results_df = pd.DataFrame(results)
            
            # Aggregate errors using Clopper-Pearson intervals
            aggregated = aggregate_errors(
                results_list=results,
                alpha_levels=cfg['alpha_levels']
            )
            
            # Add ICC column to aggregated results
            aggregated['icc'] = icc
            
            # Append to master list
            all_results.append(aggregated)
            
        except Exception as e:
            print(f"Error processing ICC={icc}: {e}", file=sys.stderr)
            # Decide whether to fail hard or skip. 
            # Given the requirement to fail loudly, we re-raise or exit.
            # However, for robustness in a loop, we might log and continue if
            # one specific ICC fails, but strictly speaking, a failed simulation
            # should be reported. Let's exit on critical failure.
            raise e

    if not all_results:
        print("No results were generated.", file=sys.stderr)
        sys.exit(1)

    # Concatenate all aggregated results
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Reorder columns for clarity
    cols = ['icc', 'method', 'alpha', 'error_rate', 'ci_lower', 'ci_upper']
    # Ensure all columns exist before selecting
    existing_cols = [c for c in cols if c in final_df.columns]
    final_df = final_df[existing_cols]

    # Save to CSV
    final_df.to_csv(args.output, index=False)
    print(f"\nSimulation complete. Results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())