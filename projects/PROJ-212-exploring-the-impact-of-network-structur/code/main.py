"""
Main orchestration script for the network synchronization impact study.
Aggregates simulation results and prepares data for regression analysis.
"""
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config, get_paths
from src.utils import setup_logging, timing_decorator
from src.simulation import process_single_network
from src.topology import compute_metrics
import src.stats as stats_module

logger = logging.getLogger(__name__)

@timing_decorator
def aggregate_simulation_results(input_path: Path, output_path: Path) -> None:
    """
    Reads results/sim_results.json and aggregates it into data/processed_metrics.csv.
    
    The CSV will contain columns:
    network_id, num_nodes, num_edges, avg_degree, clustering_coeff, 
    avg_path_length, synchronization_threshold
    
    This file is the input for the regression analysis (T025+).
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        # Handle case where data might be a single object or dict
        if isinstance(data, dict):
            data = [data]
        else:
            raise ValueError(f"Unexpected data format in {input_path}: expected list or dict")

    if len(data) == 0:
        logger.warning(f"No simulation results found in {input_path}. CSV will be empty.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'network_id', 'num_nodes', 'num_edges', 'avg_degree', 
        'clustering_coeff', 'avg_path_length', 'synchronization_threshold'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for entry in data:
            # Extract metrics
            metrics = entry.get('metrics', {})
            network_id = entry.get('network_id', 'unknown')
            threshold = entry.get('threshold')

            row = {
                'network_id': network_id,
                'num_nodes': metrics.get('num_nodes', 0),
                'num_edges': metrics.get('num_edges', 0),
                'avg_degree': metrics.get('avg_degree', 0.0),
                'clustering_coeff': metrics.get('clustering_coeff', 0.0),
                'avg_path_length': metrics.get('avg_path_length', float('inf')),
                'synchronization_threshold': threshold
            }
            writer.writerow(row)

    logger.info(f"Aggregated {len(data)} results to {output_path}")

def write_pipeline_status(status: Dict[str, Any], output_path: Path) -> None:
    """Write pipeline status to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Pipeline status written to {output_path}")

def main() -> int:
    """
    Main entry point.
    1. Loads configuration.
    2. Aggregates simulation results (T022).
    3. (Future) Triggers regression analysis if data is sufficient (T025).
    """
    config = load_config()
    paths = get_paths(config)
    
    # Setup logging
    setup_logging(config.get('logging', {}), paths['logs'])

    logger.info("Starting main pipeline orchestration.")
    start_time = time.time()

    input_results = paths['results'] / 'sim_results.json'
    output_csv = paths['data'] / 'processed_metrics.csv'
    status_file = paths['results'] / 'pipeline_status.json'

    try:
        # T022: Aggregate simulation results
        logger.info(f"Aggregating results from {input_results} to {output_csv}")
        aggregate_simulation_results(input_results, output_csv)

        # Verify output exists
        if not output_csv.exists():
            raise RuntimeError(f"Failed to create {output_csv}")

        duration = time.time() - start_time
        status = {
            "network_id": "aggregate",
            "duration": duration,
            "status": "SUCCESS",
            "output_file": str(output_csv)
        }
        write_pipeline_status(status, status_file)

        logger.info(f"Pipeline completed successfully in {duration:.2f}s")
        return 0

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        
        status = {
            "network_id": "aggregate",
            "duration": duration,
            "status": "FAILED",
            "error": str(e)
        }
        write_pipeline_status(status, status_file)
        return 1

if __name__ == "__main__":
    sys.exit(main())