import os
import json
import pickle
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
import numpy as np
from pymatgen.core import Structure
from pymatgen.io.cif import CifParser

from config import get_config
from utils import setup_logging, pin_seed

# --- Configuration ---
CONFIG = get_config()
NETWORKS_DIR = CONFIG.data_processed / "networks"
METRICS_CSV_PATH = CONFIG.data_processed / "metrics.csv"
MANIFEST_PATH = CONFIG.data_processed / "network_manifest.json"

# --- Logging Setup ---
def setup_metrics_logger(name: str = "metrics_logger") -> logging.Logger:
    logger = setup_logging(name, CONFIG.log_dir / "metrics.log")
    return logger

logger = setup_metrics_logger()

# --- Helper Functions ---
def load_graphs_from_directory(directory: Path) -> List[Tuple[str, nx.Graph]]:
    """Load all pickle graph files from a directory."""
    graphs = []
    if not directory.exists():
        logger.error(f"Directory {directory} does not exist.")
        return graphs

    for file_path in directory.glob("*.pkl"):
        try:
            with open(file_path, "rb") as f:
                graph = pickle.load(f)
                if not isinstance(graph, nx.Graph):
                    logger.warning(f"Skipping {file_path}: not a networkx.Graph")
                    continue
                graphs.append((file_path.stem, graph))
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
    return graphs

def compute_metrics_for_graph(graph: nx.Graph, material_id: str) -> Dict[str, Any]:
    """Compute network metrics for a single graph."""
    metrics = {
        "material_id": material_id,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
    }

    if graph.number_of_nodes() == 0:
        metrics["avg_degree"] = 0.0
        metrics["avg_shortest_path"] = float('nan')
        metrics["clustering_coeff"] = 0.0
        return metrics

    # Average Degree
    degrees = [d for n, d in graph.degree()]
    metrics["avg_degree"] = float(np.mean(degrees)) if degrees else 0.0

    # Largest Connected Component (LCC) metrics
    if nx.is_connected(graph):
        lcc = graph
    else:
        try:
            lcc = max(nx.connected_components(graph), key=len)
            lcc = graph.subgraph(lcc).copy()
        except Exception:
            lcc = None

    if lcc is not None and lcc.number_of_nodes() > 1:
        try:
            lengths = nx.shortest_path_length(lcc)
            # Flatten lengths
            all_lengths = [length for source_lengths in lengths.values() for length in source_lengths.values()]
            # Exclude self-loops (distance 0)
            all_lengths = [l for l in all_lengths if l > 0]
            metrics["avg_shortest_path"] = float(np.mean(all_lengths)) if all_lengths else float('nan')
        except nx.NetworkXError:
            metrics["avg_shortest_path"] = float('nan')
    else:
        metrics["avg_shortest_path"] = float('nan')

    # Clustering Coefficient
    metrics["clustering_coeff"] = float(nx.average_clustering(graph))

    return metrics

def extract_physical_descriptors(graph: nx.Graph, material_id: str, graph_metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Extract physical descriptors (unit_cell_volume, total_atom_count, mean_atomic_mass)
    associated with the graph.
    
    Note: Since the graph itself is just topology, we rely on the manifest or a 
    side-car metadata file to retrieve the physical properties. 
    However, T011 (network_manifest.json) is the source of truth for material properties 
    derived from the CIF parsing in T009/T011.
    
    We expect the manifest to contain 'properties' for each material_id.
    """
    descriptors = {
        "material_id": material_id,
        "unit_cell_volume": None,
        "total_atom_count": None,
        "mean_atomic_mass": None,
    }

    # Load manifest to find physical properties
    if not MANIFEST_PATH.exists():
        logger.warning(f"Manifest {MANIFEST_PATH} not found. Cannot extract physical descriptors.")
        return descriptors

    try:
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return descriptors

    # Find material in manifest
    material_info = None
    for item in manifest.get("materials", []):
        if item.get("material_id") == material_id:
            material_info = item
            break

    if not material_info:
        logger.warning(f"Material {material_id} not found in manifest.")
        return descriptors

    props = material_info.get("properties", {})
    
    # Map manifest keys to descriptor keys
    descriptors["unit_cell_volume"] = props.get("unit_cell_volume")
    descriptors["total_atom_count"] = props.get("total_atom_count")
    
    # Calculate mean atomic mass if not directly stored
    if "mean_atomic_mass" in props:
        descriptors["mean_atomic_mass"] = props["mean_atomic_mass"]
    elif "atomic_masses" in props:
        masses = props["atomic_masses"]
        if masses:
            descriptors["mean_atomic_mass"] = float(np.mean(masses))
    
    return descriptors

def save_metrics_to_csv(all_metrics: List[Dict[str, Any]], all_descriptors: List[Dict[str, Any]]) -> None:
    """
    Save network metrics and physical descriptors to a single CSV file.
    Physical descriptors are appended as columns with a header comment.
    """
    if not all_metrics:
        logger.warning("No metrics to save.")
        return

    # Merge metrics and descriptors by material_id
    # Create a lookup for descriptors
    desc_lookup = {d["material_id"]: d for d in all_descriptors}
    
    # Prepare rows
    rows = []
    for m in all_metrics:
        mid = m["material_id"]
        d = desc_lookup.get(mid, {})
        row = {
            **m,
            "unit_cell_volume": d.get("unit_cell_volume"),
            "total_atom_count": d.get("total_atom_count"),
            "mean_atomic_mass": d.get("mean_atomic_mass"),
        }
        rows.append(row)

    # Define columns order
    # Primary features first, then diagnostics
    primary_cols = ["material_id", "num_nodes", "num_edges", "avg_degree", "avg_shortest_path", "clustering_coeff"]
    diag_cols = ["unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
    
    # Ensure all columns are present (some might be None)
    all_cols = primary_cols + diag_cols

    # Write to CSV with header comment
    with open(METRICS_CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        # Write the diagnostic header comment as the first line
        writer.writerow(["# DIAGNOSTICS: Physical descriptors excluded from regression features"])
        # Write the header row
        writer.writerow(all_cols)
        
        # Write data rows
        for row in rows:
            data_row = [row.get(col, "") for col in all_cols]
            # Handle NaN values for CSV
            data_row = ["" if (isinstance(v, float) and np.isnan(v)) else v for v in data_row]
            writer.writerow(data_row)

    logger.info(f"Metrics and physical descriptors saved to {METRICS_CSV_PATH}")

def main():
    """Main entry point for computing metrics and extracting physical descriptors."""
    pin_seed(CONFIG.seed)
    logger.info("Starting metric computation and physical descriptor extraction.")

    # Load graphs
    graphs_data = load_graphs_from_directory(NETWORKS_DIR)
    logger.info(f"Loaded {len(graphs_data)} graphs.")

    if not graphs_data:
        logger.error("No graphs found. Exiting.")
        return

    all_metrics = []
    all_descriptors = []

    for material_id, graph in graphs_data:
        # Compute network metrics
        metrics = compute_metrics_for_graph(graph, material_id)
        all_metrics.append(metrics)

        # Extract physical descriptors
        descriptors = extract_physical_descriptors(graph, material_id)
        all_descriptors.append(descriptors)

    # Save combined results
    save_metrics_to_csv(all_metrics, all_descriptors)

    logger.info("Metric computation and descriptor extraction completed.")

if __name__ == "__main__":
    main()
