"""
Main orchestration script for the Network Synchronization Impact study.

This script:
1. Loads configuration.
2. Retrieves the list of SNAP datasets.
3. Sorts the list alphabetically (for SC-003 compliance).
4. Iterates through the first 5 networks (or fewer if available).
5. For each network:
   - Loads the graph.
   - Checks for disconnection (early exit if disconnected).
   - Computes topological metrics.
   - Runs the Kuramoto simulation to find the critical coupling threshold.
   - Aggregates results.
6. Saves the aggregated results to `results/sim_results.json`.
"""
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports
from config import load_config, get_paths
from loader import get_snap_dataset_list, load_snap_graph_from_edgelist, generate_synthetic_graph
from src.topology import compute_metrics
from src.simulation import check_disconnected, run_kuramoto_simulation
from src.utils import setup_logging, log_error, safe_exit
from data_models import SimulationResult, NetworkGraph

def process_single_network(
    dataset_id: str,
    edge_file_path: Path,
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Process a single network: load, analyze topology, run simulation.
    
    Args:
        dataset_id: Unique identifier for the dataset.
        edge_file_path: Path to the edge list file.
        config: Configuration dictionary.
        
    Returns:
        A dictionary containing the simulation results and metrics, or None if failed.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing network: {dataset_id}")
    
    start_time = time.time()
    
    try:
        # 1. Load the graph
        # The loader function is expected to handle the actual loading from the file path
        G = load_snap_graph_from_edgelist(edge_file_path)
        
        if G is None:
            logger.error(f"Failed to load graph for {dataset_id}. Skipping.")
            return None
        
        # 2. Check for disconnected components
        if check_disconnected(G):
            logger.warning(f"Graph {dataset_id} is disconnected. Skipping simulation.")
            return {
                "dataset_id": dataset_id,
                "status": "disconnected",
                "threshold": None,
                "metrics": None,
                "error": "Graph is disconnected"
            }
        
        # 3. Compute topological metrics
        logger.info(f"Computing metrics for {dataset_id}")
        metrics = compute_metrics(G)
        
        # 4. Run Kuramoto simulation
        logger.info(f"Running simulation for {dataset_id}")
        sim_result = run_kuramoto_simulation(G, config)
        
        duration = time.time() - start_time
        
        return {
            "dataset_id": dataset_id,
            "status": "success",
            "threshold": sim_result.threshold,
            "metrics": metrics,
            "duration_seconds": duration,
            "simulation_details": {
                "n_nodes": G.number_of_nodes(),
                "n_edges": G.number_of_edges(),
                "k_sweep_range": [0.0, 5.0],
                "k_step": 0.1
            }
        }
        
    except Exception as e:
        duration = time.time() - start_time
        log_error(logger, e, f"Error processing {dataset_id}")
        return {
            "dataset_id": dataset_id,
            "status": "failed",
            "threshold": None,
            "metrics": None,
            "error": str(e),
            "duration_seconds": duration
        }

def main() -> int:
    """
    Main entry point for the orchestration script.
    
    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
        
    paths = get_paths()
    
    # Ensure results directory exists
    results_dir = paths["results_dir"]
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the list of SNAP datasets
    logger.info("Fetching SNAP dataset list...")
    dataset_list = get_snap_dataset_list()
    
    if not dataset_list:
        logger.warning("No datasets found. Exiting.")
        return 0
    
    # Sort alphabetically by filename/dataset_id (SC-003 requirement)
    dataset_list.sort(key=lambda x: x.get("id", x.get("filename", "")))
    logger.info(f"Sorted {len(dataset_list)} datasets alphabetically.")
    
    # Select the first 5 networks for processing (as per T017b logic, but here in main)
    # Note: T016 is the general orchestration. T017b specifically asks for the first 5.
    # We will process the first 5 to satisfy the verification requirement.
    subset_size = 5
    subset = dataset_list[:subset_size]
    logger.info(f"Processing first {len(subset)} networks: {[d['id'] for d in subset]}")
    
    all_results = []
    total_start = time.time()
    
    for dataset_info in subset:
        dataset_id = dataset_info.get("id")
        # Assuming the loader expects the filename or path relative to data_dir
        # The loader function `load_snap_graph_from_edgelist` takes a path.
        # We need to construct the path to the edgelist file.
        # Based on typical SNAP structure, files are in data/raw/
        filename = dataset_info.get("filename")
        if not filename:
            logger.error(f"Missing filename for dataset {dataset_id}")
            continue
            
        edge_file_path = paths["raw_data_dir"] / filename
        
        if not edge_file_path.exists():
            logger.warning(f"Edge file not found for {dataset_id}: {edge_file_path}. Skipping.")
            # Optional: Generate synthetic if real missing? No, T005 handles N>=30 logic.
            # Here we just skip if file missing.
            continue
        
        result = process_single_network(dataset_id, edge_file_path, config)
        if result:
            all_results.append(result)
    
    total_duration = time.time() - total_start
    
    # Save results to JSON
    output_path = results_dir / "sim_results.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total_processed": len(all_results),
                    "total_duration_seconds": total_duration,
                    "config_seeds": config.get("seeds", {}),
                    "thresholds": config.get("thresholds", {})
                },
                "results": all_results
            }, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())