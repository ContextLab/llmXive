import os
import sys
import json
import logging
import time
import csv
from pathlib import Path

# Add the project root to the path to allow imports from code/
# This assumes the script is run from the project root or code/
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config, get_paths
from src.utils import setup_logging, timing_decorator, log_error
from src.simulation import process_single_network
from src.topology import compute_metrics
from src.validators import validate_network_list, check_disconnected_graph
from src.loader import load_real_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@timing_decorator
def process_all_networks(config: dict) -> list:
    """
    Process all networks in data/raw/:
    1. Load network
    2. Compute topological metrics
    3. Run Kuramoto simulation to find critical coupling
    4. Return list of results
    """
    paths = get_paths(config)
    raw_dir = Path(paths['data_raw'])
    results = []

    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return results

    networks = load_real_data(raw_dir)
    if not networks:
        logger.warning("No networks found in raw data directory.")
        return results

    logger.info(f"Processing {len(networks)} networks...")

    for net_data in networks:
        try:
            network_id = net_data.get('id', 'unknown')
            G = net_data.get('graph')
            
            if G is None:
                logger.warning(f"Skipping {network_id}: Graph is None")
                continue

            # Validate graph
            if not validate_network_list([{'id': network_id, 'graph': G}]):
                logger.warning(f"Skipping {network_id}: Validation failed")
                continue

            # Compute metrics
            metrics = compute_metrics(G)
            
            # Check for disconnected graph before simulation
            if check_disconnected_graph(G):
                logger.info(f"Network {network_id} is disconnected. Skipping simulation.")
                results.append({
                    'network_id': network_id,
                    'metrics': metrics,
                    'threshold': None,
                    'status': 'disconnected'
                })
                continue

            # Run simulation
            sim_result = process_single_network(G, config)
            
            results.append({
                'network_id': network_id,
                'metrics': metrics,
                'threshold': sim_result.get('threshold'),
                'status': sim_result.get('status', 'completed')
            })

        except Exception as e:
            log_error(logger, f"Error processing network {network_id}: {e}")
            results.append({
                'network_id': network_id,
                'metrics': {},
                'threshold': None,
                'status': 'error',
                'error_message': str(e)
            })

    return results

def aggregate_simulation_results(results: list, config: dict) -> None:
    """
    Aggregate simulation results into data/processed_metrics.csv
    """
    paths = get_paths(config)
    output_path = Path(paths['data_processed']) / 'processed_metrics.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not results:
        logger.warning("No results to aggregate.")
        # Write empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['network_id', 'degree', 'clustering', 'path_length', 'threshold', 'status'])
        return

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow([
            'network_id', 
            'degree', 
            'clustering', 
            'path_length', 
            'threshold', 
            'status'
        ])

        for res in results:
            metrics = res.get('metrics', {})
            writer.writerow([
                res.get('network_id'),
                metrics.get('avg_degree', ''),
                metrics.get('clustering_coeff', ''),
                metrics.get('avg_path_length', ''),
                res.get('threshold'),
                res.get('status')
            ])

    logger.info(f"Aggregated results written to {output_path}")

def main():
    config = load_config()
    setup_logging(config)
    
    logger.info("Starting pipeline...")
    
    # Process all networks
    results = process_all_networks(config)
    
    # Aggregate results
    aggregate_simulation_results(results, config)
    
    logger.info("Pipeline completed.")

if __name__ == "__main__":
    main()