import os
import json
import pickle
import logging
import csv
import math
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import from sibling modules as per API surface
from utils import setup_logging, pin_seed

def setup_metrics_logger(name: str = "metrics_logger", log_file: str = "results/metrics.log") -> logging.Logger:
    """Configure and return a logger for metrics computation."""
    logger = setup_logging(name, log_file)
    return logger

def load_graphs_from_directory(graph_dir: str) -> List[Dict[str, Any]]:
    """
    Load all graph pickle files from the specified directory.
    Returns a list of dicts: {'path': str, 'graph': networkx.Graph, 'material_id': str}
    """
    graphs = []
    graph_path = Path(graph_dir)
    if not graph_path.exists():
        raise FileNotFoundError(f"Directory not found: {graph_dir}")

    for pkl_file in graph_path.glob("*.pkl"):
        try:
            with open(pkl_file, 'rb') as f:
                graph_data = pickle.load(f)
                # Expecting structure from construct_network.py: {'graph': G, 'material_id': id, ...}
                if 'graph' in graph_data and 'material_id' in graph_data:
                    graphs.append({
                        'path': str(pkl_file),
                        'graph': graph_data['graph'],
                        'material_id': graph_data['material_id'],
                        'cif_path': graph_data.get('cif_path', '')
                    })
                else:
                    logging.warning(f"Skipping {pkl_file}: missing required keys 'graph' or 'material_id'")
        except Exception as e:
            logging.error(f"Failed to load {pkl_file}: {e}")
    return graphs

def load_thermal_conductivity_from_manifest(manifest_path: str) -> Dict[str, float]:
    """
    Load thermal conductivity data from the network manifest.
    Returns a dict: {material_id: thermal_conductivity_scalar}
    """
    thermal_data = {}
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        logging.warning(f"Manifest file not found: {manifest_path}. Thermal conductivity will be NaN.")
        return thermal_data

    with open(manifest_file, 'r') as f:
        data = json.load(f)

    for entry in data.get('materials', []):
        mat_id = entry.get('material_id')
        k_val = entry.get('thermal_conductivity_scalar')
        if mat_id and k_val is not None:
            thermal_data[mat_id] = k_val
    return thermal_data

def load_physical_descriptors_from_manifest(manifest_path: str) -> Dict[str, Dict[str, float]]:
    """
    Load physical descriptors (unit_cell_volume, total_atom_count, mean_atomic_mass) from the network manifest.
    Returns a dict: {material_id: {'unit_cell_volume': float, 'total_atom_count': int, 'mean_atomic_mass': float}}
    """
    descriptors = {}
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        logging.warning(f"Manifest file not found: {manifest_path}. Physical descriptors will be NaN.")
        return descriptors

    with open(manifest_file, 'r') as f:
        data = json.load(f)

    for entry in data.get('materials', []):
        mat_id = entry.get('material_id')
        # Extract physical descriptors if present
        if mat_id:
            descriptors[mat_id] = {
                'unit_cell_volume': entry.get('unit_cell_volume', float('nan')),
                'total_atom_count': entry.get('total_atom_count', float('nan')),
                'mean_atomic_mass': entry.get('mean_atomic_mass', float('nan'))
            }
    return descriptors

def compute_metrics_for_graph(graph, thermal_data: Dict[str, float], physical_data: Dict[str, Dict[str, float]], material_id: str) -> Dict[str, Any]:
    """
    Compute network metrics and attach thermal/physical data for a single graph.
    """
    import networkx as nx

    metrics = {
        'material_id': material_id,
        'num_nodes': graph.number_of_nodes(),
        'num_edges': graph.number_of_edges(),
        'density': nx.density(graph),
        'average_degree': 2 * graph.number_of_edges() / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0.0,
        'clustering_coefficient': nx.average_clustering(graph) if graph.number_of_nodes() > 0 else 0.0,
        'thermal_conductivity': float('nan')
    }

    # Handle disconnected graphs for shortest path
    try:
        # Largest Connected Component (LCC)
        if nx.is_connected(graph):
            metrics['average_shortest_path_length'] = nx.average_shortest_path_length(graph)
        else:
            lcc = max(nx.connected_components(graph), key=len)
            lcc_graph = graph.subgraph(lcc)
            metrics['average_shortest_path_length'] = nx.average_shortest_path_length(lcc_graph)
    except (nx.NetworkXError, ZeroDivisionError):
        metrics['average_shortest_path_length'] = float('nan')

    # Attach thermal conductivity
    if material_id in thermal_data:
        metrics['thermal_conductivity'] = thermal_data[material_id]

    # Attach physical descriptors (Diagnostic only)
    if material_id in physical_data:
        metrics['unit_cell_volume'] = physical_data[material_id]['unit_cell_volume']
        metrics['total_atom_count'] = physical_data[material_id]['total_atom_count']
        metrics['mean_atomic_mass'] = physical_data[material_id]['mean_atomic_mass']
    else:
        metrics['unit_cell_volume'] = float('nan')
        metrics['total_atom_count'] = float('nan')
        metrics['mean_atomic_mass'] = float('nan')

    return metrics

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str, manifest_path: str):
    """
    Save metrics to CSV.
    Includes a header comment for physical descriptors as diagnostics.
    """
    if not metrics_list:
        logging.warning("No metrics to save.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Define columns. Physical descriptors are last.
    # Order: material_id, network metrics, thermal, physical diagnostics
    base_cols = ['material_id', 'num_nodes', 'num_edges', 'density', 'average_degree', 
                 'average_shortest_path_length', 'clustering_coefficient', 'thermal_conductivity']
    diag_cols = ['unit_cell_volume', 'total_atom_count', 'mean_atomic_mass']
    all_cols = base_cols + diag_cols

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write diagnostic header comment as per task requirement
        # The comment should be at the top of the file
        with open(output_path, 'w') as f:
            f.write("# DIAGNOSTICS: Physical descriptors excluded from regression features\n")
            # Write header
            writer.writerow(all_cols)
            
            # Write data
            for row in metrics_list:
                # Ensure all keys exist in row, fill with NaN if missing
                row_data = [row.get(col, float('nan')) for col in all_cols]
                writer.writerow(row_data)

def main():
    """Main entry point for metrics computation."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute network metrics and correlate with thermal conductivity.")
    parser.add_argument('--input', type=str, default='data/processed/networks/', help='Input directory for graph pickles')
    parser.add_argument('--output', type=str, default='data/processed/metrics.csv', help='Output CSV path')
    parser.add_argument('--manifest', type=str, default='data/processed/network_manifest.json', help='Path to network manifest')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()

    # Setup logging
    logger = setup_metrics_logger()
    logger.info(f"Starting metrics computation. Input: {args.input}, Output: {args.output}")

    # Pin seed
    pin_seed(args.seed)

    # Check input directory
    if not os.path.exists(args.input):
        logger.error(f"Input directory not found: {args.input}")
        sys.exit(1)

    # Load graphs
    graphs = load_graphs_from_directory(args.input)
    logger.info(f"Loaded {len(graphs)} graphs.")

    if not graphs:
        logger.error("No valid graphs found in input directory.")
        sys.exit(1)

    # Load thermal conductivity
    thermal_data = load_thermal_conductivity_from_manifest(args.manifest)
    logger.info(f"Loaded thermal conductivity for {len(thermal_data)} materials.")

    # Load physical descriptors (T015b requirement)
    physical_data = load_physical_descriptors_from_manifest(args.manifest)
    logger.info(f"Loaded physical descriptors for {len(physical_data)} materials.")

    # Compute metrics
    metrics_list = []
    for item in graphs:
        try:
            m = compute_metrics_for_graph(
                item['graph'], 
                thermal_data, 
                physical_data, 
                item['material_id']
            )
            metrics_list.append(m)
        except Exception as e:
            logger.error(f"Failed to compute metrics for {item['material_id']}: {e}")

    # Save to CSV
    save_metrics_to_csv(metrics_list, args.output, args.manifest)
    logger.info(f"Metrics saved to {args.output}")

if __name__ == "__main__":
    main()
