"""
Main orchestration script for the network synchronization simulation pipeline.

This script:
1. Loads configuration and sets up logging.
2. Iterates over available networks (real or synthetic fallback for testing).
3. Computes topological metrics.
4. Runs Kuramoto simulations to find critical coupling strength.
5. Aggregates results into `results/sim_results.json`.
"""
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports from the project structure
from config import load_config, get_paths
from loader import load_real_data, generate_synthetic_graph
from src.topology import compute_metrics
from src.simulation import run_kuramoto_simulation, check_disconnected
from src.utils import setup_logging, compute_checksum, log_error, safe_exit

def process_single_network(graph_id: str, G: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single network: compute metrics, run simulation, return result dict.
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    result_entry = {
        "id": graph_id,
        "status": "pending",
        "metrics": {},
        "simulation": {},
        "duration": 0.0,
        "error": None
    }

    try:
        # 1. Check connectivity
        if check_disconnected(G):
            logger.warning(f"Graph {graph_id} is disconnected. Skipping simulation.")
            result_entry["status"] = "disconnected"
            result_entry["metrics"] = compute_metrics(G)
            result_entry["simulation"] = {"threshold": None, "reason": "disconnected"}
            return result_entry

        # 2. Compute topological metrics
        logger.info(f"Computing metrics for {graph_id}...")
        metrics = compute_metrics(G)
        result_entry["metrics"] = metrics

        # 3. Run simulation
        logger.info(f"Running Kuramoto simulation for {graph_id}...")
        sim_config = config.get("simulation", {})
        sim_result = run_kuramoto_simulation(
            G, 
            k_range=sim_config.get("k_range", [0, 5, 0.1]),
            threshold_r=sim_config.get("threshold_r", 0.8),
            threshold_t=sim_config.get("threshold_t", 100)
        )
        
        result_entry["simulation"] = {
            "threshold": sim_result.get("critical_k"),
            "order_at_threshold": sim_result.get("order_at_threshold"),
            "final_order": sim_result.get("final_order"),
            "steps": sim_result.get("steps", 0)
        }
        result_entry["status"] = "success"

    except Exception as e:
        log_error(logger, f"Error processing {graph_id}", e)
        result_entry["status"] = "failed"
        result_entry["error"] = str(e)
    
    result_entry["duration"] = time.time() - start_time
    return result_entry

def main():
    """
    Main entry point for the orchestration script.
    """
    # Load config and paths
    config = load_config()
    paths = get_paths(config)
    results_dir = paths.get("results", Path("results"))
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("Starting main orchestration pipeline.")
    
    start_total = time.time()
    all_results = []
    
    # Load real data (or synthetic if < 10 files found, per T005 logic)
    # Note: load_real_data handles the fetching and counting logic.
    # It returns a list of (id, graph) tuples.
    networks = load_real_data(config, paths)
    
    if not networks:
        logger.warning("No networks available to process. Exiting.")
        # Even if empty, we write an empty results file to satisfy the artifact requirement
        output_path = results_dir / "sim_results.json"
        with open(output_path, "w") as f:
            json.dump({"networks": [], "total_duration": 0.0}, f, indent=2)
        return

    logger.info(f"Processing {len(networks)} networks.")
    
    for graph_id, G in networks:
        entry = process_single_network(graph_id, G, config)
        all_results.append(entry)
        
    total_duration = time.time() - start_total
    
    # Save results
    output_path = results_dir / "sim_results.json"
    final_report = {
        "networks": all_results,
        "total_duration": total_duration,
        "checksum": compute_checksum(all_results)
    }
    
    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Pipeline complete. Results saved to {output_path}")
    safe_exit(0)

if __name__ == "__main__":
    main()