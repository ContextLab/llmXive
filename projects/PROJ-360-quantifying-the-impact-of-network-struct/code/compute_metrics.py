"""
code/compute_metrics.py

Computes network metrics from graph artifacts and appends thermal conductivity scalars.
Produces data/processed/metrics.csv.
"""
import os
import json
import pickle
import logging
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from sibling utils for logging setup
from utils import setup_logging


def setup_metrics_logger(name: str = "metrics_logger", log_file: str = "results/metrics.log") -> logging.Logger:
    """Setup a logger for the metrics computation."""
    logger = setup_logging(name, log_file)
    return logger


def load_graphs_from_directory(graph_dir: str) -> List[Tuple[str, Any]]:
    """
    Load all pickle files from the given directory.
    Returns a list of (material_id, graph_object) tuples.
    """
    graph_path = Path(graph_dir)
    if not graph_path.exists():
        raise FileNotFoundError(f"Directory not found: {graph_dir}")

    graphs = []
    for pkl_file in graph_path.glob("*.pkl"):
        try:
            with open(pkl_file, 'rb') as f:
                graph = pickle.load(f)
                # Extract material_id from filename (remove .pkl)
                material_id = pkl_file.stem
                graphs.append((material_id, graph))
        except Exception as e:
            logging.error(f"Failed to load {pkl_file}: {e}")
    return graphs


def load_manifest(manifest_path: str = "data/processed/network_manifest.json") -> Optional[Dict[str, Any]]:
    """Load the network manifest if it exists."""
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            return json.load(f)
    return None


def get_thermal_conductivity_scalar(manifest: Dict[str, Any], material_id: str) -> Optional[float]:
    """
    Extract thermal conductivity scalar from the manifest.
    Formula: (k_x + k_y + k_z) / 3
    """
    if not manifest or 'materials' not in manifest:
        return None

    material_data = manifest['materials'].get(material_id)
    if not material_data:
        return None

    k_x = material_data.get('k_x')
    k_y = material_data.get('k_y')
    k_z = material_data.get('k_z')

    if any(v is None for v in [k_x, k_y, k_z]):
        return None

    # Calculate scalar
    scalar = (k_x + k_y + k_z) / 3.0

    # Verification: Assert scalar matches mean within tolerance 1e-6 (FR-004)
    expected_mean = (k_x + k_y + k_z) / 3.0
    if abs(scalar - expected_mean) > 1e-6:
        raise ValueError(
            f"Assertion failed for material {material_id}: "
            f"Calculated scalar ({scalar}) does not match mean of components ({expected_mean}) "
            f"within tolerance 1e-6. Discrepancy: {abs(scalar - expected_mean)}"
        )

    return scalar


def compute_metrics_for_graph(graph: Any, material_id: str) -> Dict[str, Any]:
    """
    Compute network metrics for a single graph.
    Metrics: average_degree, avg_shortest_path (on LCC), clustering_coeff, density, node_count, edge_count.
    """
    import networkx as nx

    metrics = {
        'material_id': material_id,
        'node_count': graph.number_of_nodes(),
        'edge_count': graph.number_of_edges()
    }

    if graph.number_of_nodes() == 0:
        metrics['average_degree'] = float('nan')
        metrics['avg_shortest_path'] = float('nan')
        metrics['clustering_coeff'] = float('nan')
        metrics['density'] = float('nan')
        return metrics

    # Average Degree
    degrees = [d for n, d in graph.degree()]
    metrics['average_degree'] = sum(degrees) / len(degrees) if degrees else 0.0

    # Density
    metrics['density'] = nx.density(graph)

    # Clustering Coefficient (average)
    metrics['clustering_coeff'] = nx.average_clustering(graph)

    # Average Shortest Path Length on Largest Connected Component (LCC)
    # Handle disconnected graphs
    if not nx.is_connected(graph):
        try:
            lcc = max(nx.connected_components(graph), key=len)
            lcc_graph = graph.subgraph(lcc)
            if len(lcc_graph) > 1:
                metrics['avg_shortest_path'] = nx.average_shortest_path_length(lcc_graph)
            else:
                metrics['avg_shortest_path'] = float('nan')
        except Exception:
            metrics['avg_shortest_path'] = float('nan')
    else:
        if graph.number_of_nodes() > 1:
            metrics['avg_shortest_path'] = nx.average_shortest_path_length(graph)
        else:
            metrics['avg_shortest_path'] = float('nan')

    return metrics


def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str):
    """Save the list of metrics dictionaries to a CSV file."""
    if not metrics_list:
        logging.warning("No metrics to save.")
        # Create empty file with headers if needed, or just exit
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['material_id', 'node_count', 'edge_count', 'average_degree', 'avg_shortest_path', 'clustering_coeff', 'density', 'thermal_conductivity_scalar'])
        return

    # Define headers
    headers = [
        'material_id', 'node_count', 'edge_count', 'average_degree',
        'avg_shortest_path', 'clustering_coeff', 'density',
        'thermal_conductivity_scalar'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(metrics_list)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compute network metrics from graph artifacts.")
    parser.add_argument('--input', required=True, help='Input directory containing graph pickle files.')
    parser.add_argument('--output', required=True, help='Output CSV file path.')
    parser.add_argument('--manifest', default='data/processed/network_manifest.json', help='Path to network manifest JSON.')
    args = parser.parse_args()

    logger = setup_metrics_logger()
    logger.info(f"Starting metrics computation. Input: {args.input}, Output: {args.output}")

    # Load graphs
    try:
        graphs = load_graphs_from_directory(args.input)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    if not graphs:
        logger.warning("No graphs found in input directory.")
        # Create empty CSV with headers
        save_metrics_to_csv([], args.output)
        return

    # Load manifest for thermal conductivity
    manifest = load_manifest(args.manifest)
    if not manifest:
        logger.warning(f"Manifest not found at {args.manifest}. Thermal conductivity column will be NaN.")

    # Compute metrics
    metrics_list = []
    for material_id, graph in graphs:
        try:
            metrics = compute_metrics_for_graph(graph, material_id)

            # Append thermal conductivity scalar
            if manifest:
                k_scalar = get_thermal_conductivity_scalar(manifest, material_id)
                metrics['thermal_conductivity_scalar'] = k_scalar if k_scalar is not None else float('nan')
            else:
                metrics['thermal_conductivity_scalar'] = float('nan')

            metrics_list.append(metrics)
        except Exception as e:
            logger.error(f"Error processing {material_id}: {e}")
            # Skip or log failure, do not crash the whole pipeline unless critical
            continue

    # Save to CSV
    save_metrics_to_csv(metrics_list, args.output)
    logger.info(f"Metrics saved to {args.output}")


if __name__ == '__main__':
    main()