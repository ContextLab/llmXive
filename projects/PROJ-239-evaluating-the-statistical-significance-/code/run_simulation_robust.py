"""
Robust Simulation Runner Script.

Executes the simulation for cluster-robust methods (Cluster-Robust T-Test
and Block Permutation) across a range of ICC values.

Output:
    data/derived/robustResults.csv
"""
import argparse
import sys
import os
import numpy as np
import pandas as pd

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import load_config, set_seed, validate_config, parse_cli_args
from code.simulation_runner import run_robust_simulation
from code.analysis import aggregate_errors, select_ci_method


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run robust simulation for A/B test significance with non-independent observations."
    )
    parser.add_argument(
        "--icc",
        type=float,
        default=None,
        help="Single ICC value to test. If provided, overrides range/step."
    )
    parser.add_argument(
        "--icc-range",
        type=float,
        nargs=2,
        metavar=("START", "END"),
        default=None,
        help="Range of ICC values [start, end] to test."
    )
    parser.add_argument(
        "--icc-step",
        type=float,
        default=None,
        help="Step size for ICC range."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of simulation iterations per ICC value."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    parser.add_argument(
        "--alpha-list",
        type=float,
        nargs="+",
        default=None,
        help="List of alpha levels to test (e.g., 0.01 0.05 0.10)."
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

    # Load base config
    cfg = load_config()

    # Override with CLI args if provided
    if args.icc is not None:
        cfg['icc'] = args.icc
        cfg['icc_range'] = None
        cfg['icc_step'] = None
    elif args.icc_range is not None:
        cfg['icc_range'] = args.icc_range
        if args.icc_step is not None:
            cfg['icc_step'] = args.icc_step
    elif args.icc_step is not None:
        cfg['icc_step'] = args.icc_step

    if args.alpha_list is not None:
        cfg['alpha_levels'] = args.alpha_list

    if args.iterations is not None:
        cfg['n_iterations'] = args.iterations

    if args.seed is not None:
        cfg['seed'] = args.seed

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Set seed
    set_seed(cfg['seed'])

    # Determine ICC values to run
    if 'icc' in cfg and cfg['icc'] is not None:
        icc_values = [cfg['icc']]
    else:
        start = cfg.get('icc_range', [0.0, 0.5])[0]
        end = cfg.get('icc_range', [0.0, 0.5])[1]
        step = cfg.get('icc_step', 0.1)
        icc_values = np.arange(start, end + step/2, step).tolist() # Include end

    print(f"Starting robust simulation with {len(icc_values)} ICC values...")
    print(f"ICC values: {icc_values}")
    print(f"Iterations per value: {cfg['n_iterations']}")
    print(f"Alpha levels: {cfg['alpha_levels']}")

    all_results = []

    for icc in icc_values:
        print(f"Running simulation for ICC={icc}...")
        try:
            results = run_robust_simulation(
                icc=icc,
                n_iterations=cfg['n_iterations'],
                seed=cfg['seed'] + int(icc * 1000), # Offset seed per ICC
                alpha_levels=cfg['alpha_levels']
            )
            all_results.extend(results)
        except Exception as e:
            print(f"Error running simulation for ICC={icc}: {e}", file=sys.stderr)
            # Continue with next ICC or exit? For robustness, we log and continue
            # But for strict correctness, maybe we should fail. Let's fail loudly.
            sys.exit(1)

    if not all_results:
        print("No results generated.", file=sys.stderr)
        sys.exit(1)

    # Convert to DataFrame
    df = pd.DataFrame(all_results)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to CSV
    df.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")
    print(f"Total rows: {len(df)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())