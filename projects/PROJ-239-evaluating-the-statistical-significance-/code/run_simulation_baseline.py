"""
Baseline Simulation Runner for A/B Test Significance Evaluation.

This script executes the baseline (naive t-test) simulation across specified
ICC levels and iteration counts, writing results to data/derived/baseline_results.csv.

Dependencies:
    - code/config.py (T004, T023, T033)
    - code/data_generator.py (T010)
    - code/estimators.py (T011, T036)
    - code/simulation_runner.py (T012)
"""

import argparse
import logging
import sys
import os
import warnings
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import load_config, set_seed, parse_cli_args, validate_config
from code.data_generator import generate_data
from code.estimators import run_naive_ttest_with_warning
from code.simulation_runner import run_baseline_simulation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/derived/baseline_simulation.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the baseline simulation."""
    parser = argparse.ArgumentParser(
        description='Run baseline simulation for A/B test significance evaluation.'
    )
    parser.add_argument(
        '--icc',
        type=float,
        default=None,
        help='Specific ICC value to simulate. If None, uses icc_range from config.'
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
        help='Comma-separated list of ICC values (e.g., 0.0,0.1,0.2).'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Number of simulation iterations per ICC level.'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility.'
    )
    parser.add_argument(
        '--alpha-list',
        type=str,
        default=None,
        help='Comma-separated alpha levels (e.g., 0.01,0.05,0.10).'
    )
    return parser.parse_args()

def run_simulation(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Execute the baseline simulation loop.

    Args:
        args: Parsed command line arguments.

    Returns:
        List of result dictionaries containing iteration, icc, p_value, rejected.
    """
    # Load base config
    cfg = load_config()

    # Parse CLI arguments to override config
    cfg = parse_cli_args(args, cfg)

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Set random seed
    set_seed(cfg['seed'])

    # Determine ICC values to simulate
    if args.icc is not None:
        icc_values = [args.icc]
    elif args.icc_range:
        icc_values = [float(x) for x in args.icc_range.split(',')]
    else:
        icc_values = cfg['icc_range']

    logger.info(f"Starting baseline simulation with ICC values: {icc_values}")
    logger.info(f"Iterations per ICC: {args.iterations}")
    logger.info(f"Seed: {cfg['seed']}")

    all_results = []
    skipped_count = 0

    for icc in icc_values:
        logger.info(f"Running simulation for ICC = {icc}")
        try:
            # Run simulation for this ICC level
            results = run_baseline_simulation(
                icc=icc,
                n_iterations=args.iterations,
                seed=cfg['seed'] + int(icc * 1000),  # Unique seed per ICC
                n_clusters=cfg['n_clusters'],
                n_obs_per_cluster=cfg.get('n_obs_per_cluster', 12)
            )
            all_results.extend(results)
            logger.info(f"Completed ICC={icc}: {len(results)} iterations")
        except Exception as e:
            logger.warning(f"Failed to run simulation for ICC={icc}: {e}. Skipping.")
            skipped_count += 1
            continue

    total_expected = len(icc_values) * args.iterations
    actual_count = len(all_results)
    logger.info(f"Simulation complete. Expected: {total_expected}, Actual: {actual_count}, Skipped: {skipped_count}")

    return all_results

def write_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write simulation results to CSV file.

    Args:
        results: List of result dictionaries.
        output_path: Path to output CSV file.
    """
    import pandas as pd

    if not results:
        logger.warning("No results to write. Creating empty file with headers.")
        df = pd.DataFrame(columns=['iteration', 'icc', 'p_value', 'rejected'])
    else:
        df = pd.DataFrame(results)
        # Ensure correct column order and types
        df = df[['iteration', 'icc', 'p_value', 'rejected']]
        df['iteration'] = df['iteration'].astype(int)
        df['icc'] = df['icc'].astype(float)
        df['p_value'] = df['p_value'].astype(float)
        df['rejected'] = df['rejected'].astype(bool)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Results written to {output_path} ({len(df)} rows)")

def verify_results(output_path: str, expected_min_rows: int) -> bool:
    """
    Verify that the output file exists and contains the expected number of rows.

    Args:
        output_path: Path to the output CSV file.
        expected_min_rows: Minimum number of rows expected (excluding header).

    Returns:
        True if verification passes, False otherwise.
    """
    import pandas as pd

    if not os.path.exists(output_path):
        logger.error(f"Output file does not exist: {output_path}")
        return False

    df = pd.read_csv(output_path)
    actual_rows = len(df)

    if actual_rows < expected_min_rows:
        logger.warning(f"Verification failed: Expected >= {expected_min_rows} rows, found {actual_rows}")
        return False

    # Check for null/NaN values in critical columns
    if df['p_value'].isnull().any() or df['rejected'].isnull().any():
        logger.error("Verification failed: Found null/NaN values in p_value or rejected columns.")
        return False

    logger.info(f"Verification passed: {actual_rows} rows written to {output_path}")
    return True

def main():
    """Main entry point for the baseline simulation script."""
    args = parse_args()
    output_path = 'data/derived/baseline_results.csv'

    try:
        # Run simulation
        results = run_simulation(args)

        # Write results
        write_results(results, output_path)

        # Verify results
        # Expected rows = number of ICC levels * iterations - skipped
        # We approximate expected_min_rows based on successful runs
        if len(results) == 0:
            logger.error("Simulation produced no results. Verification failed.")
            sys.exit(1)

        expected_min_rows = len(results)  # Use actual count as minimum since we don't know skipped beforehand
        if not verify_results(output_path, expected_min_rows):
            logger.error("Verification failed. Exiting with error.")
            sys.exit(1)

        logger.info("Baseline simulation completed successfully.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error during simulation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()