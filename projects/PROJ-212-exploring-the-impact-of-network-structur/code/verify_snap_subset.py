"""
Verification script for SC-003:
Sort SNAP dataset list alphabetically, run simulations on the first 5 networks,
and generate results/verification_report.json.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project modules (relative to code/)
from loader import get_snap_dataset_list, load_snap_graph_from_edgelist
from simulation import check_disconnected, run_kuramoto_simulation
from data_models import SimulationResult
from config import load_config, get_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_simulation_on_graph(
    graph_id: str,
    edge_list_path: Path
) -> Optional[Dict[str, Any]]:
    """
    Load a graph from an edge list file and run the Kuramoto simulation.
    Returns a dictionary with the graph ID and the critical coupling threshold,
    or None if the graph is invalid or simulation fails.
    """
    logger.info(f"Processing graph: {graph_id}")
    try:
        # Load the graph
        graph = load_snap_graph_from_edgelist(edge_list_path)
        
        if graph is None or graph.number_of_nodes() == 0:
            logger.warning(f"Graph {graph_id} is empty or failed to load.")
            return None

        # Check for disconnected components
        if check_disconnected(graph):
            logger.warning(f"Graph {graph_id} is disconnected. Skipping simulation.")
            return {
                "graph_id": graph_id,
                "threshold": float('inf'),
                "status": "disconnected"
            }

        # Run simulation
        logger.info(f"Running Kuramoto simulation on {graph_id} (nodes={graph.number_of_nodes()})")
        start_time = time.time()
        
        result: SimulationResult = run_kuramoto_simulation(graph)
        
        elapsed = time.time() - start_time
        logger.info(f"Simulation for {graph_id} completed in {elapsed:.2f}s. Threshold: {result.critical_coupling}")

        return {
            "graph_id": graph_id,
            "threshold": result.critical_coupling,
            "status": "success",
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "duration_seconds": elapsed
        }

    except Exception as e:
        logger.error(f"Error processing graph {graph_id}: {e}", exc_info=True)
        return {
            "graph_id": graph_id,
            "threshold": None,
            "status": "error",
            "error_message": str(e)
        }


def main():
    """
    Main entry point for the verification script.
    1. Load config to get paths.
    2. Get the full list of SNAP datasets.
    3. Sort the list alphabetically by filename.
    4. Select the first 5 networks.
    5. Run simulations on them.
    6. Save the report to results/verification_report.json.
    """
    config = load_config()
    paths = get_paths()
    
    # Ensure results directory exists
    results_dir = paths["results"]
    results_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Fetching SNAP dataset list...")
    dataset_list = get_snap_dataset_list()
    
    if not dataset_list:
        logger.error("No datasets found in the SNAP repository.")
        return

    # Sort alphabetically by filename (the 'id' field in our list usually corresponds to the filename)
    # The get_snap_dataset_list returns a list of dicts with 'id' and 'url'
    sorted_datasets = sorted(dataset_list, key=lambda x: x['id'])
    
    logger.info(f"Total datasets available: {len(sorted_datasets)}. Selecting first 5.")
    top_5_datasets = sorted_datasets[:5]
    
    report_entries = []
    
    for dataset in top_5_datasets:
        graph_id = dataset['id']
        url = dataset['url']
        
        # We need to map the ID back to a local file or download it.
        # Assuming the loader downloads to data/raw/ or similar based on config.
        # For this verification, we assume load_snap_graph_from_edgelist handles the path resolution
        # or we construct the path based on the ID if it's already downloaded.
        # Given T005/T006 context, let's assume the files are in data/raw/ named <id>.txt
        # or we rely on the loader to fetch if missing.
        # However, load_snap_graph_from_edgelist expects a Path.
        # We will construct the expected path based on standard conventions if not handled internally.
        
        # Let's assume the loader's internal logic handles the URL to Path mapping if we pass the ID,
        # but the signature requires a Path.
        # We will construct the path assuming the file is in data/raw/
        # If the file doesn't exist, the loader might fail, which is acceptable for a "fail loudly" approach 
        # unless we implement a download step here.
        # To be safe and self-contained, we'll try to derive the local path.
        
        # Standard convention: data/raw/<id>.txt or similar.
        # Let's assume the loader expects the file to exist.
        # If the file is not present, we might need to download it first.
        # For this script, we will assume the data is already fetched or the loader handles it.
        # But the signature is load_snap_graph_from_edgelist(edge_list_path: Path).
        
        # Let's try to find the file in the data directory.
        # We'll search for a file matching the ID in data/raw/
        data_dir = paths.get("raw_data", paths["data"]) # Fallback
        if not isinstance(data_dir, Path):
            data_dir = Path(data_dir)
        
        possible_paths = [
            data_dir / f"{graph_id}.txt",
            data_dir / f"{graph_id}.edge",
            data_dir / graph_id
        ]
        
        found_path = None
        for p in possible_paths:
            if p.exists():
                found_path = p
                break
        
        if not found_path:
            # If not found, we might need to download. 
            # But T005 handles the main loader. This is a verification script.
            # We will log a warning and skip if the file is not local.
            logger.warning(f"Local file for {graph_id} not found at {data_dir}. Skipping.")
            report_entries.append({
                "graph_id": graph_id,
                "threshold": None,
                "status": "skipped_file_not_found",
                "reason": f"File not found in {data_dir}"
            })
            continue

        result = run_simulation_on_graph(graph_id, found_path)
        if result:
            report_entries.append(result)

    # Generate the report
    report = {
        "task_id": "T017b",
        "sc_requirement": "SC-003",
        "description": "Verification report for first 5 SNAP networks (alphabetically sorted)",
        "total_datasets_available": len(sorted_datasets),
        "networks_processed": len(report_entries),
        "results": report_entries
    }

    output_path = results_dir / "verification_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Verification report saved to {output_path}")


if __name__ == "__main__":
    main()