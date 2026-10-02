"""
Task T020b: THETA SWEEP EXECUTION

Executes the generic orchestrator (T020a) specifically for the theta grid 
defined in T040a. Outputs raw results to data/processed/mc_results.csv 
and data/processed/convergence_data.json.

Dependencies: T020a (Generic Orchestrator), T040a (Grid Definition)
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import from existing API surface
from analysis.threshold_sweep import run_threshold_sweep, generate_sweep_grid
from utils.config import get_project_paths

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_theta_sweep_execution():
    """
    Execute the theta sweep using the generic orchestrator.
    
    This function:
    1. Loads the theta grid defined in T040a
    2. Runs the generic orchestrator (T020a) for each configuration
    3. Outputs raw results to data/processed/mc_results.csv
    4. Outputs convergence data to data/processed/convergence_data.json
    """
    paths = get_project_paths()
    
    # Define the theta grid as per T040a
    # Using a representative range around the theoretical threshold (theta_c = 1.0)
    theta_values = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
    N_values = [500, 1000, 2000]
    seeds = [42, 123, 456]
    
    logger.info(f"Starting theta sweep execution with {len(theta_values)} theta values, "
               f"{len(N_values)} matrix sizes, and {len(seeds)} seeds")
    
    # Generate the sweep grid
    sweep_grid = generate_sweep_grid(theta_values, N_values, seeds)
    logger.info(f"Generated {len(sweep_grid)} configurations for sweep")
    
    # Run the threshold sweep
    results = run_threshold_sweep(sweep_grid)
    
    if not results:
        logger.error("No results produced by threshold sweep")
        return False
    
    logger.info(f"Produced {len(results)} results from sweep")
    
    # Ensure output directories exist
    processed_dir = Path(paths['data_processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Output 1: mc_results.csv
    csv_path = processed_dir / 'mc_results.csv'
    logger.info(f"Writing {len(results)} results to {csv_path}")
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['run_id', 'N', 'theta', 'seed', 'eigenvalue_top', 'outlier_flag']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                'run_id': result.get('run_id', ''),
                'N': result.get('N', 0),
                'theta': result.get('theta', 0.0),
                'seed': result.get('seed', 0),
                'eigenvalue_top': result.get('eigenvalue_top', 0.0),
                'outlier_flag': result.get('outlier_flag', False)
            })
    
    logger.info(f"Successfully wrote mc_results.csv with {len(results)} rows")
    
    # Output 2: convergence_data.json
    json_path = processed_dir / 'convergence_data.json'
    logger.info(f"Writing convergence data to {json_path}")
    
    convergence_data = {
        'metadata': {
            'theta_values': theta_values,
            'N_values': N_values,
            'seeds': seeds,
            'total_runs': len(results),
            'timestamp': str(Path(csv_path).stat().st_mtime)
        },
        'results': results
    }
    
    with open(json_path, 'w') as jsonfile:
        json.dump(convergence_data, jsonfile, indent=2)
    
    logger.info(f"Successfully wrote convergence_data.json")
    
    # Summary statistics
    outlier_count = sum(1 for r in results if r.get('outlier_flag', False))
    logger.info(f"Sweep complete: {outlier_count}/{len(results)} runs detected outliers")
    
    return True

def main():
    """Main entry point for T020b execution."""
    parser = argparse.ArgumentParser(
        description='Execute theta sweep for phase transition detection (T020b)'
    )
    parser.add_argument(
        '--theta-grid',
        type=str,
        default=None,
        help='Optional: Path to custom theta grid JSON file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        success = run_theta_sweep_execution()
        if success:
            logger.info("T020b execution completed successfully")
            sys.exit(0)
        else:
            logger.error("T020b execution failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"T020b execution failed with exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()