"""
Script to run transient phase metric extraction on simulation results.

This script loads simulation results, extracts transient phase metrics,
and saves the aggregated report.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from code.src.simulation.metrics import (
    extract_transient_phase_metrics,
    calculate_relaxation_time,
    aggregate_transient_report,
    save_transient_metrics
)
from code.src.simulation.stability import check_numerical_stability

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_simulation_results(input_path: str) -> Dict[str, Any]:
    """Load simulation results from JSON file."""
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")
    
    with open(input_file, 'r') as f:
        return json.load(f)


def extract_all_transient_metrics(simulation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract transient phase metrics for all simulation runs.
    
    Args:
        simulation_results: Dictionary containing simulation results.
        
    Returns:
        List of transient phase reports for each simulation run.
    """
    reports = []
    
    # Handle different possible structures
    runs = simulation_results.get('runs', [simulation_results])
    
    for run in runs:
        simulation_id = run.get('simulation_id', 'unknown')
        logger.info(f"Processing transient metrics for simulation: {simulation_id}")
        
        # Extract necessary data
        energy_history = run.get('energy_history', [])
        spins_history = run.get('spins_history', [])
        time_steps = run.get('time_steps', list(range(len(energy_history))))
        adjacency_matrix = run.get('adjacency_matrix')
        
        if adjacency_matrix and isinstance(adjacency_matrix, list):
            adjacency_matrix = np.array(adjacency_matrix)
        
        if not energy_history or not spins_history:
            logger.warning(f"Missing energy or spins history for {simulation_id}, skipping")
            continue
        
        # Convert spins_history to numpy arrays if needed
        if spins_history and isinstance(spins_history[0], list):
            spins_history = [np.array(s) for s in spins_history]
        
        # Extract transient metrics
        transient_metrics = extract_transient_phase_metrics(
            energy_history,
            spins_history,
            time_steps,
            adjacency_matrix
        )
        
        # Calculate relaxation time
        relaxation_metrics = calculate_relaxation_time(energy_history, time_steps)
        
        # Perform stability check
        stability_check = check_numerical_stability(energy_history)
        
        # Aggregate report
        report = aggregate_transient_report(
            simulation_id,
            transient_metrics,
            relaxation_metrics,
            stability_check
        )
        
        reports.append(report)
    
    return reports


def main():
    """Main function to run transient phase metric extraction."""
    parser = argparse.ArgumentParser(
        description="Extract transient phase metrics from simulation results"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/analysis/simulation_results.json",
        help="Path to simulation results JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/transient_phase_report.json",
        help="Path to save transient phase report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load simulation results
        logger.info(f"Loading simulation results from {args.input}")
        simulation_results = load_simulation_results(args.input)
        
        # Extract transient metrics
        logger.info("Extracting transient phase metrics")
        reports = extract_all_transient_metrics(simulation_results)
        
        if not reports:
            logger.warning("No transient metrics extracted. Check input data.")
            # Create an empty report structure
            reports = [{
                'simulation_id': 'none',
                'timestamp': str(np.datetime64('now')),
                'summary': {
                    'total_steps': 0,
                    'transient_steps': 0,
                    'equilibrium_reached': False
                }
            }]
        
        # Save aggregated report
        logger.info(f"Saving transient phase report to {args.output}")
        save_transient_metrics({
            'transient_reports': reports,
            'total_simulations': len(reports),
            'equilibrium_reached_count': sum(1 for r in reports if r.get('summary', {}).get('equilibrium_reached', False))
        }, args.output)
        
        logger.info("Transient phase metric extraction completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during transient phase metric extraction: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())