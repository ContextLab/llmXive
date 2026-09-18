import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import networkx as nx

from src.loader import get_snap_dataset_list, load_snap_graph_from_edgelist
from src.simulation import check_disconnected, run_kuramoto_simulation
from src.utils import setup_logging

logger = logging.getLogger(__name__)

def run_simulation_on_graph(graph: nx.Graph, network_id: str) -> Optional[float]:
    """
    Run Kuramoto simulation on a single graph and return the critical coupling threshold.
    Returns None if the graph is disconnected (threshold is infinity).
    """
    if check_disconnected(graph):
        logger.info(f"Graph {network_id} is disconnected. Skipping simulation (threshold = infinity).")
        return None

    try:
        # Run simulation with default parameters from config (K sweep 0 to 5, step 0.1)
        result = run_kuramoto_simulation(graph)
        return result.threshold
    except Exception as e:
        logger.error(f"Simulation failed for {network_id}: {e}")
        return None

def main():
    """
    Main entry point for T017b:
    1. Verify presence of SNAP files (or fetch via loader).
    2. Sort file list in data/raw/ (filtering .mtx, .csv, .gml) alphabetically.
    3. Run simulations on the first N networks (or all if small).
    4. Generate results/verification_report.json.
    """
    setup_logging()
    logger.info("Starting SNAP verification and simulation pipeline (T017b)...")

    # 1. Ensure data/raw directory exists and attempt to fetch real data if needed
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Attempt to get list of SNAP datasets (this may trigger fetch logic in loader)
    # We rely on loader.py to handle the real data fetching and validation
    dataset_list = get_snap_dataset_list()
    logger.info(f"Retrieved {len(dataset_list)} available SNAP datasets.")

    # 2. Scan data/raw for existing supported files
    supported_extensions = {'.mtx', '.csv', '.gml'}
    existing_files = []
    for ext in supported_extensions:
        existing_files.extend(raw_dir.glob(f"*{ext}"))
    
    # Filter to only those that correspond to known SNAP IDs if possible
    # For now, we assume any file in data/raw is a candidate
    # Sort alphabetically by filename as per requirement
    existing_files.sort(key=lambda p: p.name)
    
    if not existing_files:
        logger.warning("No network files found in data/raw/. Attempting to fetch a small subset.")
        # Fetch a small, manageable subset of real SNAP data to satisfy the "real data" constraint
        # We fetch the first 3 available datasets to ensure we have something to run
        # This is a controlled fetch, not synthetic generation
        count = 0
        for dataset in dataset_list[:3]:
            try:
                # The loader function handles the actual download and saving
                # We assume it saves to data/raw/
                load_snap_graph_from_edgelist(dataset['id']) 
                count += 1
                if count >= 3: break
            except Exception as e:
                logger.warning(f"Failed to fetch {dataset['id']}: {e}")
                continue
        
        # Re-scan
        existing_files = []
        for ext in supported_extensions:
            existing_files.extend(raw_dir.glob(f"*{ext}"))
        existing_files.sort(key=lambda p: p.name)

    if not existing_files:
        logger.error("Failed to acquire any real network data. Aborting.")
        raise RuntimeError("No real data available after fetch attempt.")

    logger.info(f"Processing {len(existing_files)} network files.")

    # 3. Run simulations
    results = []
    for file_path in existing_files:
        network_id = file_path.stem  # filename without extension
        logger.info(f"Processing network: {network_id}")

        try:
            # Load graph
            ext = file_path.suffix.lower()
            if ext == '.gml':
                G = nx.read_gml(file_path)
            elif ext == '.mtx':
                G = nx.read_matrix_market(file_path)
            elif ext == '.csv':
                # Assume edgelist format for CSV
                G = nx.read_edgelist(file_path)
            else:
                logger.warning(f"Skipping unsupported extension: {ext}")
                continue

            # Run simulation
            threshold = run_simulation_on_graph(G, network_id)
            
            results.append({
                "id": network_id,
                "threshold": threshold
            })
        except Exception as e:
            logger.error(f"Error processing {network_id}: {e}")
            # Record as null threshold for failed runs
            results.append({
                "id": network_id,
                "threshold": None
            })

    # 4. Generate verification report
    report_path = Path("results/verification_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_data = {"networks": results}
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Verification report generated at {report_path}")
    logger.info("T017b completed successfully.")

if __name__ == "__main__":
    main()
