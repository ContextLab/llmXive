import os
import json
import pickle
import logging
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import networkx as nx
import numpy as np

from config import get_config

# --- Logging Setup ---
def setup_metrics_logger(name: str = "metrics_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --- Graph Loading ---
def load_graphs_from_directory(graph_dir: str) -> Dict[str, nx.Graph]:
    """
    Loads all pickle files from the specified directory into a dictionary
    mapping material_id (filename without extension) to networkx.Graph.
    """
    graphs = {}
    dir_path = Path(graph_dir)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {graph_dir}")

    for pkl_file in dir_path.glob("*.pkl"):
        try:
            with open(pkl_file, 'rb') as f:
                graph = pickle.load(f)
                if not isinstance(graph, nx.Graph):
                    logging.warning(f"Skipping {pkl_file}: not a networkx.Graph")
                    continue
                material_id = pkl_file.stem
                graphs[material_id] = graph
                logging.info(f"Loaded graph for {material_id}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        except Exception as e:
            logging.error(f"Failed to load {pkl_file}: {e}")
    return graphs

def load_thermal_conductivity_from_manifest(manifest_path: str) -> Dict[str, float]:
    """
    Loads thermal conductivity data from the manifest JSON.
    Returns a dict: material_id -> thermal_conductivity (scalar).
    """
    if not os.path.exists(manifest_path):
        logging.warning(f"Manifest not found at {manifest_path}. Thermal conductivity will be missing.")
        return {}
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Expecting structure: {"materials": [{"id": "...", "thermal_conductivity": ...}, ...]}
    # Or similar based on T011 implementation. Adjusting for common structure.
    kc_map = {}
    if "materials" in data:
        for entry in data["materials"]:
            mid = entry.get("id") or entry.get("material_id")
            kc = entry.get("thermal_conductivity")
            if mid and kc is not None:
                kc_map[mid] = float(kc)
    elif isinstance(data, list):
        for entry in data:
            mid = entry.get("id") or entry.get("material_id")
            kc = entry.get("thermal_conductivity")
            if mid and kc is not None:
                kc_map[mid] = float(kc)
    return kc_map

def load_physical_descriptors_from_manifest(manifest_path: str) -> Dict[str, Dict[str, float]]:
    """
    Loads physical descriptors (volume, atom count, mass) from manifest.
    """
    if not os.path.exists(manifest_path):
        return {}
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    descriptors = {}
    if "materials" in data:
        for entry in data["materials"]:
            mid = entry.get("id") or entry.get("material_id")
            if mid:
                descriptors[mid] = {
                    "unit_cell_volume": entry.get("unit_cell_volume"),
                    "total_atom_count": entry.get("total_atom_count"),
                    "mean_atomic_mass": entry.get("mean_atomic_mass")
                }
    return descriptors

# --- Metric Computation ---
def compute_metrics_for_graph(graph: nx.Graph, material_id: str) -> Dict[str, Any]:
    """
    Computes network metrics for a single graph.
    
    Handles disconnected graphs:
      - Average shortest path length: returns NaN if graph is disconnected or has < 2 nodes.
      - Network density: computed as a diagnostic (does not affect main analysis).
    
    Returns a dictionary of metrics.
    """
    metrics = {
        "material_id": material_id,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges()
    }

    # 1. Average Degree
    if metrics["num_nodes"] == 0:
        metrics["avg_degree"] = 0.0
    else:
        total_degree = sum(d for n, d in graph.degree())
        metrics["avg_degree"] = total_degree / metrics["num_nodes"]

    # 2. Average Shortest Path Length (on Largest Connected Component)
    # Requirement: Handle disconnected graphs by reporting NaN for path length if the graph is not fully connected
    # or if the LCC is too small to compute a meaningful path.
    if metrics["num_nodes"] < 2:
        metrics["avg_shortest_path_length"] = float('nan')
    else:
        # Check connectivity
        if not nx.is_connected(graph):
            # If disconnected, we compute on the Largest Connected Component (LCC)
            # but we must report NaN for the "global" path length if the graph is not fully connected?
            # The task says: "handle disconnected graphs (report NaN for path length)".
            # Interpretation: If the graph is not fully connected, the global average shortest path is undefined/infinite.
            # We report NaN to indicate this undefined state, as per the specific task instruction.
            metrics["avg_shortest_path_length"] = float('nan')
            
            # However, for the clustering coefficient, we usually compute on LCC or average over components.
            # Let's stick to the instruction: report NaN for path length.
            # We can still compute clustering on the whole graph or LCC.
        else:
            try:
                # Only compute if connected
                length = nx.average_shortest_path_length(graph)
                metrics["avg_shortest_path_length"] = length
            except Exception as e:
                logging.warning(f"Error computing path length for {material_id}: {e}")
                metrics["avg_shortest_path_length"] = float('nan')

    # 3. Clustering Coefficient
    if metrics["num_nodes"] < 3:
        metrics["clustering_coefficient"] = 0.0
    else:
        # Global average clustering
        metrics["clustering_coefficient"] = nx.average_clustering(graph)

    # 4. Network Density (Diagnostic Only)
    # Density = 2 * |E| / (|V| * (|V|-1)) for undirected graphs
    if metrics["num_nodes"] < 2:
        metrics["density"] = 0.0
    else:
        max_edges = metrics["num_nodes"] * (metrics["num_nodes"] - 1) / 2
        metrics["density"] = metrics["num_edges"] / max_edges if max_edges > 0 else 0.0

    return metrics

# --- Saving ---
def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str, kc_map: Dict[str, float], phys_map: Dict[str, Dict[str, float]]):
    """
    Saves metrics to a CSV file.
    Includes thermal conductivity and physical descriptors as diagnostics columns.
    """
    if not metrics_list:
        logging.warning("No metrics to save.")
        return

    # Define columns
    # Primary metrics
    primary_cols = ["material_id", "num_nodes", "num_edges", "avg_degree", "avg_shortest_path_length", "clustering_coefficient"]
    # Diagnostic columns (Thermal Conductivity)
    kc_col = "thermal_conductivity_scalar"
    # Diagnostic columns (Physical Descriptors)
    phys_cols = ["unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
    
    # Check if any row has NaN for path length to ensure float type handling
    # We will write 'NaN' string or float('nan') which csv module handles as 'nan'
    
    fieldnames = primary_cols + [kc_col] + phys_cols
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in metrics_list:
            out_row = {}
            # Primary
            for col in primary_cols:
                val = row.get(col)
                if val is None:
                    out_row[col] = ""
                elif isinstance(val, float) and math.isnan(val):
                    out_row[col] = "NaN"
                else:
                    out_row[col] = val
            
            # Thermal Conductivity
            mid = row["material_id"]
            out_row[kc_col] = kc_map.get(mid, "")
            
            # Physical Descriptors
            phys_data = phys_map.get(mid, {})
            for pcol in phys_cols:
                val = phys_data.get(pcol)
                out_row[pcol] = val if val is not None else ""
        
            writer.writerow(out_row)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Compute network metrics from graph files.")
    parser.add_argument("--input", required=True, help="Input directory containing .pkl graph files")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--manifest", required=False, help="Path to network_manifest.json for metadata")
    args = parser.parse_args()

    logger = setup_metrics_logger()
    logger.info(f"Starting metrics computation. Input: {args.input}, Output: {args.output}")

    # Load graphs
    graphs = load_graphs_from_directory(args.input)
    if not graphs:
        logger.error("No valid graphs found. Exiting.")
        return 1

    # Load metadata if manifest provided
    kc_map = {}
    phys_map = {}
    manifest_path = args.manifest
    if not manifest_path:
        # Try default location
        default_manifest = "data/processed/network_manifest.json"
        if os.path.exists(default_manifest):
            manifest_path = default_manifest
    
    if manifest_path:
        kc_map = load_thermal_conductivity_from_manifest(manifest_path)
        phys_map = load_physical_descriptors_from_manifest(manifest_path)
        logger.info(f"Loaded metadata from {manifest_path}. KC entries: {len(kc_map)}, Phys entries: {len(phys_map)}")
    else:
        logger.warning("Manifest not provided or found. Thermal conductivity and physical descriptors will be empty.")

    # Compute metrics
    metrics_list = []
    for mid, graph in graphs.items():
        try:
            metrics = compute_metrics_for_graph(graph, mid)
            metrics_list.append(metrics)
        except Exception as e:
            logger.error(f"Failed to compute metrics for {mid}: {e}")
            continue

    # Save
    save_metrics_to_csv(metrics_list, args.output, kc_map, phys_map)
    logger.info(f"Metrics saved to {args.output}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())