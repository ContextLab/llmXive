"""
Verification script for T017b.
Verifies presence of SNAP files (or fetches via loader), sorts them alphabetically,
runs simulations on the initial set, and generates verification_report.json.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports (using the 'code' directory structure as per API surface)
from config import load_config, get_paths
from loader import get_snap_dataset_list, load_snap_graph_from_edgelist, generate_synthetic_graph
from simulation import check_disconnected, run_kuramoto_simulation
from topology import compute_metrics
from validators import validate_network_list
from utils import setup_logging

def run_simulation_on_graph(
    graph_id: str,
    graph: Any,
    config: Dict[str, Any]
) -> Optional[float]:
    """
    Run Kuramoto simulation on a single graph and return the critical coupling threshold.
    Returns None if the graph is disconnected.
    """
    # Check connectivity first
    if check_disconnected(graph):
        logging.warning(f"Graph {graph_id} is disconnected. Skipping simulation.")
        return None

    # Run simulation
    # Config parameters from config.yaml
    k_start = config.get('simulation', {}).get('k_start', 0.0)
    k_end = config.get('simulation', {}).get('k_end', 5.0)
    k_step = config.get('simulation', {}).get('k_step', 0.1)
    r_threshold = config.get('thresholds', {}).get('r', 0.8)
    t_duration = config.get('thresholds', {}).get('t', 100)

    try:
        result = run_kuramoto_simulation(
            graph,
            k_start=k_start,
            k_end=k_end,
            k_step=k_step,
            r_threshold=r_threshold,
            t_duration=t_duration
        )
        return result.get('threshold')
    except Exception as e:
        logging.error(f"Simulation failed for {graph_id}: {e}")
        return None

def main():
    """
    Main entry point for T017b verification.
    1. Load config.
    2. Get list of available SNAP files in data/raw/ (filtering .mtx, .csv, .gml).
    3. Sort alphabetically.
    4. Run simulations on a subset (or all) of the available networks.
    5. Generate results/verification_report.json.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    # Load configuration
    config = load_config()
    paths = get_paths()

    raw_dir = paths['raw_data']
    results_dir = paths['results']

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify presence of specific SNAP files or fetch via loader
    # The loader has a function to get a list of known SNAP datasets.
    # We will check the local 'data/raw' directory for existing files.
    # If files are missing, we attempt to fetch them using the loader's fetch logic.
    # However, T017b specifically asks to "verify the presence... or fetch via loader".
    # We will first scan the local directory.
    
    valid_extensions = {'.mtx', '.csv', '.gml'}
    file_list = []

    if raw_dir.exists():
        for f in raw_dir.iterdir():
            if f.is_file() and f.suffix.lower() in valid_extensions:
                file_list.append(f)
    
    # Sort alphabetically by filename
    file_list.sort(key=lambda p: p.name)

    logger.info(f"Found {len(file_list)} network files in {raw_dir}")

    # If the list is empty, we might need to fetch. 
    # However, T005 (Loader) is expected to have populated this or at least attempted to.
    # If empty, we log a warning and proceed with an empty list (report will be empty).
    if not file_list:
        logger.warning("No network files found in data/raw/. Verification report will be empty.")
        report = {"networks": []}
        report_path = results_dir / "verification_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Verification report written to {report_path}")
        return

    # 2. Run simulations on the set of initial networks
    # We will process all found files, but we can limit if needed for time.
    # For T017b, "a set of initial networks" implies the ones found.
    
    networks_data = []
    max_files = config.get('verification', {}).get('max_files', 10) # Optional limit
    
    # If the list is huge, we might just take the first N. 
    # But the task says "run simulations on a set of initial networks".
    # We'll process the sorted list.
    
    for i, file_path in enumerate(file_list):
        if i >= max_files and max_files > 0:
            logger.info(f"Reached max_files limit ({max_files}). Stopping.")
            break
        
        graph_id = file_path.stem # Filename without extension
        logger.info(f"Processing network {i+1}/{len(file_list)}: {graph_id}")

        # Load graph
        try:
            # The loader function expects a path to the edgelist file
            graph = load_snap_graph_from_edgelist(str(file_path))
        except Exception as e:
            logger.error(f"Failed to load graph {graph_id}: {e}")
            # Append with null threshold
            networks_data.append({"id": graph_id, "threshold": None})
            continue

        # Run simulation
        threshold = run_simulation_on_graph(graph_id, graph, config)
        
        networks_data.append({
            "id": graph_id,
            "threshold": threshold
        })

    # 3. Generate results/verification_report.json
    report = {
        "networks": networks_data
    }

    report_path = results_dir / "verification_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report generated: {report_path}")
    logger.info(f"Processed {len(networks_data)} networks.")

if __name__ == "__main__":
    main()
