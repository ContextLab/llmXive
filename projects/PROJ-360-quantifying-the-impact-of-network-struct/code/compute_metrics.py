import os
import json
import pickle
import logging
import csv
import math
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import networkx as nx
from networkx.algorithms.components import connected_components, number_connected_components

# Import shared utilities
from config import Config, get_config
from utils import setup_logging, pin_seed

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
NETWORKS_DIR = DATA_PROCESSED_DIR / "networks"
METRICS_CSV_PATH = DATA_PROCESSED_DIR / "metrics.csv"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-360-quantifying-the-impact-of-network-struct.yaml"
MANIFEST_PATH = DATA_PROCESSED_DIR / "networks" / "manifest.json"
METADATA_PATH = DATA_PROCESSED_DIR / "metadata.yaml"

# Logger setup
logger = setup_logging("metrics_logger", "results/metrics.log")

def load_graphs_from_directory(directory: Path) -> List[Dict[str, Any]]:
    """Load all pickle graphs from the directory."""
    graphs = []
    if not directory.exists():
        logger.error(f"Directory {directory} does not exist.")
        return graphs

    for file_path in directory.glob("*.pkl"):
        try:
            with open(file_path, 'rb') as f:
                graph_data = pickle.load(f)
                # Ensure it's a networkx graph
                if isinstance(graph_data, nx.Graph):
                    material_id = file_path.stem
                    graphs.append({
                        "material_id": material_id,
                        "graph": graph_data,
                        "file_path": file_path
                    })
                else:
                    logger.warning(f"Skipping {file_path}: not a networkx.Graph")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    return graphs

def load_manifest() -> Dict[str, Any]:
    """Load the network manifest if it exists."""
    if not MANIFEST_PATH.exists():
        logger.warning(f"Manifest not found at {MANIFEST_PATH}. Returning empty manifest.")
        return {"materials": {}}
    
    try:
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return {"materials": {}}

def compute_lcc_metrics(graph: nx.Graph) -> Dict[str, float]:
    """
    Compute average shortest path length on the Largest Connected Component (LCC).
    If the graph is disconnected, we MUST operate on the LCC to avoid infinite distances.
    Returns path_length, clustering_coefficient.
    """
    if graph.number_of_nodes() == 0:
        return {"path_length": float('nan'), "clustering": float('nan')}
    
    # Identify Connected Components
    components = list(connected_components(graph))
    if not components:
        return {"path_length": float('nan'), "clustering": float('nan')}
    
    # Find Largest Connected Component
    lcc = max(components, key=len)
    lcc_graph = graph.subgraph(lcc).copy()
    
    # Calculate Average Shortest Path Length on LCC
    # Note: nx.average_shortest_path_length requires a connected graph
    try:
        path_length = nx.average_shortest_path_length(lcc_graph)
    except Exception as e:
        logger.warning(f"Could not compute path length for LCC: {e}")
        path_length = float('nan')
    
    # Calculate Clustering Coefficient (average)
    clustering = nx.average_clustering(lcc_graph)
    
    return {
        "path_length": path_length,
        "clustering": clustering
    }

def compute_metrics_for_graph(graph_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Compute metrics for a single graph: avg_degree, path_length (on LCC), clustering.
    """
    graph = graph_data["graph"]
    material_id = graph_data["material_id"]

    if graph.number_of_nodes() < 2:
        logger.warning(f"Graph for {material_id} has < 2 nodes. Skipping metrics.")
        return None

    # 1. Average Degree
    avg_degree = sum(dict(graph.degree()).values()) / graph.number_of_nodes()

    # 2. & 3. Path Length and Clustering (on LCC)
    lcc_metrics = compute_lcc_metrics(graph)

    return {
        "material_id": material_id,
        "avg_degree": avg_degree,
        "path_length": lcc_metrics["path_length"],
        "clustering": lcc_metrics["clustering"]
    }

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: Path):
    """Save metrics to a CSV file."""
    if not metrics_list:
        logger.warning("No metrics to save.")
        # Still write header to ensure file exists if expected, though T013 requires data rows.
        # However, if we have no data, we can't produce a valid CSV with data rows.
        # We will write the header to be safe, but log the issue.
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["material_id", "avg_degree", "path_length", "clustering"])
            writer.writeheader()
        return

    fieldnames = ["material_id", "avg_degree", "path_length", "clustering"]
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_list:
            # Handle NaN values for CSV
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    clean_row[k] = "NaN"
                else:
                    clean_row[k] = v
            writer.writerow(clean_row)
    
    logger.info(f"Saved {len(metrics_list)} metrics to {output_path}")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_artifact_hash(file_path: Path, state_file: Path):
    """
    Update the state YAML file with the checksum of the generated artifact.
    This satisfies Constitution Principle V (Versioning Discipline).
    """
    import yaml
    
    if not state_file.exists():
        logger.warning(f"State file {state_file} does not exist. Creating it.")
        state_data = {"artifact_hashes": {}}
    else:
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load state file: {e}")
            state_data = {"artifact_hashes": {}}
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    checksum = compute_sha256(file_path)
    relative_path = str(file_path.relative_to(PROJECT_ROOT))
    state_data["artifact_hashes"][relative_path] = checksum
    
    # Atomic write
    temp_path = state_file.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    os.replace(temp_path, state_file)
    logger.info(f"Updated state file with checksum for {relative_path}: {checksum}")

def main():
    """Main entry point for T013."""
    logger.info("Starting T013: Compute Network Metrics")
    
    # Load graphs
    graphs = load_graphs_from_directory(NETWORKS_DIR)
    if not graphs:
        logger.error("No graphs found in data/processed/networks/. Cannot compute metrics.")
        # Create empty CSV with header to satisfy file existence check, though data is missing
        METRICS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["material_id", "avg_degree", "path_length", "clustering"])
            writer.writeheader()
        return

    logger.info(f"Loaded {len(graphs)} graphs.")

    # Compute metrics
    metrics_list = []
    for graph_data in graphs:
        result = compute_metrics_for_graph(graph_data)
        if result:
            metrics_list.append(result)
    
    if not metrics_list:
        logger.error("No valid metrics computed.")
        METRICS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_CSV_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["material_id", "avg_degree", "path_length", "clustering"])
            writer.writeheader()
        return

    # Save to CSV
    METRICS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_metrics_to_csv(metrics_list, METRICS_CSV_PATH)

    # Update State
    update_state_artifact_hash(METRICS_CSV_PATH, STATE_FILE_PATH)
    
    logger.info("T013 completed successfully.")

if __name__ == "__main__":
    main()