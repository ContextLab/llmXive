"""
Script to run the baseline simulation for evaluating statistical significance
of A/B test results with non-independent observations.

This script implements Task T014:
- CLI accepting --icc, --iterations, --seed, and optional --icc-step.
- Uses config loader (T004) and writes data/derived/baseline_results.csv.
- Schema: iteration, icc, p_value, rejected (bool).
- Error Handling: Logs warnings and skips failed iterations.
- Verification: Ensures output file exists with correct row count.
"""
import argparse
import logging
import sys
import os
import warnings
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from code.config import (
    load_config,
    set_seed,
    ICC_RANGE,
    DEFAULT_N_CLUSTERS,
    DEFAULT_SEED,
    parse_cli_args
)
from code.simulation_runner import run_baseline_simulation
from code.analysis import aggregate_errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run baseline simulation for A/B test significance evaluation.'
    )
    parser.add_argument(
        '--icc',
        type=float,
        default=None,
        help='Specific ICC value to run. If None, runs all values in ICC_RANGE.'
    )
    parser.add_argument(
        '--icc-step',
        type=float,
        default=None,
        help='Step size for ICC range. Overrides config default.'
    )
    parser.add_argument(
        '--icc-range',
        type=str,
        default=None,
        help='Comma-separated list of ICC values. Overrides config default.'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=1000,
        help='Number of iterations per ICC value (default: 1000).'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=DEFAULT_SEED,
        help='Random seed for reproducibility (default: 42).'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/derived/baseline_results.csv',
        help='Output file path (default: data/derived/baseline_results.csv).'
    )
    parser.add_argument(
        '--alpha-list',
        type=str,
        default=None,
        help='Comma-separated alpha levels for aggregation (default: 0.01,0.05,0.10).'
    )

    return parser.parse_args()

def main() -> int:
    """Main entry point for the baseline simulation script."""
    args = parse_args()

    # Load base configuration
    cfg = load_config()

    # Apply CLI overrides
    if args.icc_range:
        try:
            icc_range_vals = [float(x.strip()) for x in args.icc_range.split(',')]
            cfg['icc_range'] = icc_range_vals
        except ValueError:
            logger.error(f"Invalid ICC range format: {args.icc_range}")
            return 1

    if args.icc_step:
        cfg['icc_step'] = args.icc_step

    if args.alpha_list:
        try:
            alpha_vals = [float(x.strip()) for x in args.alpha_list.split(',')]
            cfg['alpha_levels'] = alpha_vals
        except ValueError:
            logger.error(f"Invalid alpha list format: {args.alpha_list}")
            return 1

    # Handle single ICC override
    if args.icc is not None:
        cfg['icc_range'] = [args.icc]

    # Set seed
    set_seed(args.seed)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Starting baseline simulation with ICC range: {cfg['icc_range']}")
    logger.info(f"Iterations per ICC: {args.iterations}")
    logger.info(f"Seed: {args.seed}")

    all_results = []
    total_iterations = len(cfg['icc_range']) * args.iterations
    completed_iterations = 0

    for icc in cfg['icc_range']:
        logger.info(f"Running simulation for ICC = {icc}")
        try:
            # Run simulation for this ICC
            iteration_results = run_baseline_simulation(
                icc=icc,
                n_iterations=args.iterations,
                seed=args.seed + int(icc * 1000),  # Vary seed slightly per ICC
                n_clusters=cfg.get('n_clusters', DEFAULT_N_CLUSTERS)
            )

            # Process results
            for i, res in enumerate(iteration_results):
                if res.get('success', False):
                    all_results.append({
                        'iteration': i,
                        'icc': icc,
                        'p_value': res['p_value'],
                        'rejected': res['rejected']
                    })
                    completed_iterations += 1
                else:
                    logger.warning(
                        f"Iteration {i} for ICC={icc} failed: {res.get('error', 'Unknown error')}"
                    )

        except Exception as e:
            logger.error(f"Failed to run simulation for ICC={icc}: {str(e)}")
            # Continue to next ICC rather than crashing
            continue

    if not all_results:
        logger.error("No successful iterations completed. Check logs for errors.")
        return 1

    # Create DataFrame
    df = pd.DataFrame(all_results)

    # Write to CSV
    df.to_csv(args.output, index=False)
    logger.info(f"Wrote {len(df)} results to {args.output}")

    # Verification
    expected_rows = len(cfg['icc_range']) * args.iterations
    if len(df) != expected_rows:
        logger.warning(
            f"Verification: Expected {expected_rows} rows, but wrote {len(df)}. "
            f"Some iterations may have failed."
        )
    else:
        logger.info(f"Verification passed: Output contains exactly {len(df)} rows.")

    logger.info("Baseline simulation completed successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())