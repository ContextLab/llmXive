import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import load_config, get_paths
from src.loader import load_real_data
from src.topology import compute_metrics
from src.simulation import find_critical_coupling, process_single_network
from src.utils import setup_logging, timing_decorator, log_error
from src.verify_snap import main as run_verification

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@timing_decorator
def process_network_graph(graph_id: str, graph_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single network graph: compute topology and run simulation.
    """
    try:
        # Compute topological metrics
        metrics = compute_metrics(graph_data['graph'])
        
        # Run Kuramoto simulation to find critical coupling
        # Pass the graph and configuration parameters
        result = process_single_network(graph_data['graph'], config)
        
        return {
            "network_id": graph_id,
            "metrics": metrics,
            "threshold": result.get('threshold'),
            "status": result.get('status')
        }
    except Exception as e:
        logger.error(f"Error processing graph {graph_id}: {e}")
        return {
            "network_id": graph_id,
            "metrics": None,
            "threshold": None,
            "status": "error",
            "error": str(e)
        }

def main():
    """
    Main orchestration script for the pipeline.
    """
    config = load_config()
    paths = get_paths()
    
    # Setup logging
    setup_logging(config)
    
    logger.info("Starting the network synchronization analysis pipeline.")
    start_time = time.time()
    
    # Load real data
    logger.info("Loading real data...")
    try:
        network_list = load_real_data(paths['data_raw'], config)
    except Exception as e:
        logger.error(f"Failed to load real data: {e}")
        # If loading fails, we might still want to generate an empty results file
        # or exit gracefully. Let's log and exit.
        log_error(e, paths['results_dir'] / 'pipeline_errors.log')
        return 1

    if not network_list:
        logger.warning("No networks loaded. Exiting.")
        # Create an empty results file to indicate completion
        results_path = paths['results_dir'] / 'sim_results.json'
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump([], f)
        return 0

    logger.info(f"Loaded {len(network_list)} networks.")
    
    all_results = []
    
    for graph_id, graph_data in network_list:
        logger.info(f"Processing network: {graph_id}")
        result = process_network_graph(graph_id, graph_data, config)
        all_results.append(result)
    
    # Save results
    results_path = paths['results_dir'] / 'sim_results.json'
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Simulation results saved to {results_path}")
    
    # Run verification step (T017b)
    logger.info("Running verification step (T017b)...")
    run_verification()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Log pipeline status
    status_path = paths['results_dir'] / 'pipeline_status.json'
    status_data = {
        "network_id": "aggregate",
        "duration": duration,
        "status": "SUCCESS",
        "networks_processed": len(all_results)
    }
    
    with open(status_path, 'w') as f:
        json.dump(status_data, f, indent=2)
    
    logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
