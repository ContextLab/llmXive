"""
Robust Simulation Runner Script.

This script executes the robust simulation loop for evaluating A/B test results
with non-independent observations. It runs the cluster-robust t-test and block
permutation test across specified ICC levels and iterations, logging results to CSV.

It depends on:
  - code/simulation_runner.py (for run_robust_simulation)
  - code/analysis.py (for aggregate_errors)
  - code/config.py (for configuration)
"""
import argparse
import logging
import os
import sys
import warnings
from typing import List, Dict, Any

# Add project root to path to allow relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import load_config, set_seed, parse_cli_args, validate_config
from simulation_runner import run_robust_simulation, run_baseline_simulation
from analysis import aggregate_errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(project_root, 'data', 'simulation_robust.log'))
    ]
)
logger = logging.getLogger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run robust simulation for A/B test significance with clustered data.'
    )
    parser.add_argument(
        '--icc',
        type=float,
        default=None,
        help='Specific ICC value to simulate. If None, uses icc_range from config.'
    )
    parser.add_argument(
        '--icc-range',
        type=str,
        default=None,
        help='Comma-separated list of ICC values (e.g., "0.0,0.1,0.2"). Overrides config.'
    )
    parser.add_argument(
        '--icc-step',
        type=float,
        default=None,
        help='Step size for ICC range generation. Overrides config.'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=1000,
        help='Number of simulation iterations per ICC level.'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to output CSV file. Defaults to data/derived/robustResults.csv.'
    )
    parser.add_argument(
        '--alpha',
        type=str,
        default=None,
        help='Comma-separated list of alpha levels (e.g., "0.01,0.05,0.10"). Overrides config.'
    )
    return parser.parse_args()

def main() -> int:
    """
    Main entry point for the robust simulation script.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    args = parse_args()

    # Load base configuration
    try:
        cfg = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Override config with CLI arguments
    if args.icc_range:
        cfg['icc_range'] = [float(x) for x in args.icc_range.split(',')]
    if args.icc_step:
        cfg['icc_step'] = args.icc_step
    if args.icc is not None:
        cfg['icc_range'] = [args.icc]
    if args.alpha:
        cfg['alpha_levels'] = [float(x) for x in args.alpha.split(',')]
    
    cfg['n_iterations'] = args.iterations
    cfg['seed'] = args.seed

    # Validate configuration
    try:
        validate_config(cfg)
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return 1

    # Set random seed
    set_seed(cfg['seed'])

    # Determine output path
    output_path = args.output or os.path.join(project_root, 'data', 'derived', 'robustResults.csv')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    logger.info(f"Starting robust simulation with ICC range: {cfg['icc_range']}")
    logger.info(f"Iterations per ICC: {cfg['n_iterations']}")
    logger.info(f"Output file: {output_path}")

    all_results = []

    try:
        for icc in cfg['icc_range']:
            logger.info(f"Running simulation for ICC={icc}")
            
            # Run the robust simulation
            # This function returns a list of dicts: [{iteration, icc, method, p_value, rejected}, ...]
            results = run_robust_simulation(
                icc=icc,
                n_iterations=cfg['n_iterations'],
                seed=cfg['seed'] + int(icc * 1000), # Offset seed per ICC to ensure variety but reproducibility
                n_clusters=cfg['n_clusters'],
                n_obs_per_cluster=cfg.get('n_obs_per_cluster', 10)
            )
            
            all_results.extend(results)
            logger.info(f"Completed ICC={icc}, processed {len(results)} iterations")

        if not all_results:
            logger.warning("No results were generated. Check simulation parameters.")
            # Write empty file with headers to avoid downstream crashes
            import pandas as pd
            df = pd.DataFrame(columns=['iteration', 'icc', 'method', 'p_value', 'rejected'])
            df.to_csv(output_path, index=False)
            logger.info(f"Wrote empty results to {output_path}")
            return 0

        # Convert to DataFrame and save
        import pandas as pd
        df = pd.DataFrame(all_results)
        
        # Ensure column types are correct
        if 'rejected' in df.columns:
            df['rejected'] = df['rejected'].astype(bool)
        if 'p_value' in df.columns:
            df['p_value'] = df['p_value'].astype(float)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

        # Optional: Compute and log aggregate errors if requested or for verification
        # Note: The task T021 specifically asks for the simulation script that writes robustResults.csv.
        # Aggregation is typically a separate step (T020/T025), but we can log a summary here.
        if 'alpha_levels' in cfg:
            summary = aggregate_errors(all_results, cfg['alpha_levels'])
            logger.info("Aggregated error rates computed (summary):")
            logger.info(summary.to_string())

        return 0

    except Exception as e:
        logger.exception(f"Simulation failed with error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())