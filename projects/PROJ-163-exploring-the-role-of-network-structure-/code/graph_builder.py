import logging
import networkx as nx
import numpy as np
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def build_coupling_graph(coupling_map: List[List[int]]) -> nx.Graph:
    """
    Build an undirected NetworkX graph from a coupling map.
    The coupling map is a list of directed edges [source, target].
    We treat them as undirected for topology analysis.
    """
    G = nx.Graph()
    if not coupling_map:
        return G

    for edge in coupling_map:
        if len(edge) == 2:
            u, v = edge
            G.add_edge(u, v)
    return G

def compute_shortest_path_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute average shortest path length and diameter.
    Handles disconnected graphs by analyzing the largest connected component.
    """
    if G.number_of_nodes() == 0:
        return {"avg_shortest_path": float('nan'), "diameter": float('nan')}

    # Handle disconnected graphs
    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        G_lcc = G.subgraph(largest_cc).copy()
    else:
        G_lcc = G

    if G_lcc.number_of_nodes() < 2:
        return {"avg_shortest_path": float('nan'), "diameter": float('nan')}

    try:
        avg_path = nx.average_shortest_path_length(G_lcc)
        diam = nx.diameter(G_lcc)
    except nx.NetworkXError:
        avg_path = float('nan')
        diam = float('nan')

    return {"avg_shortest_path": avg_path, "diameter": diam}

def compute_clustering_and_assortativity(G: nx.Graph) -> Dict[str, float]:
    """
    Compute global clustering coefficient and degree assortativity.
    """
    if G.number_of_nodes() == 0:
        return {"clustering_coeff": float('nan'), "assortativity": float('nan')}

    try:
        # average_clustering is the standard global clustering coefficient
        clustering = nx.average_clustering(G)
        assortativity = nx.degree_assortativity_coefficient(G)
    except ZeroDivisionError:
        clustering = float('nan')
        assortativity = float('nan')

    return {"clustering_coeff": clustering, "assortativity": assortativity}

def compute_edge_betweenness_and_spectral_gap(G: nx.Graph) -> Dict[str, float]:
    """
    Compute edge betweenness centrality mean and spectral gap of Laplacian.
    """
    if G.number_of_nodes() == 0:
        return {"edge_betweenness_mean": float('nan'), "spectral_gap": float('nan')}

    # Edge Betweenness
    try:
        edge_betw = nx.edge_betweenness_centrality(G)
        mean_betw = np.mean(list(edge_betw.values())) if edge_betw else 0.0
    except ZeroDivisionError:
        mean_betw = 0.0

    # Spectral Gap (Laplacian)
    # Spectral gap is the difference between the two smallest eigenvalues of the Laplacian.
    # For a connected graph, the smallest is 0. The gap is the second smallest.
    # For disconnected, the second smallest is 0, so gap is 0.
    try:
        L = nx.laplacian_matrix(G).todense()
        eigenvalues = sorted(np.linalg.eigvals(L))
        eigenvalues = [ev.real for ev in eigenvalues]
        eigenvalues.sort()

        if len(eigenvalues) < 2:
            spectral_gap = 0.0
        else:
            spectral_gap = max(0.0, eigenvalues[1] - eigenvalues[0])
    except Exception:
        spectral_gap = float('nan')

    return {"edge_betweenness_mean": mean_betw, "spectral_gap": spectral_gap}

def process_device_coupling_map(coupling_map: List[List[int]]) -> Dict[str, Any]:
    """
    Compute all graph metrics for a single device's coupling map.
    """
    G = build_coupling_graph(coupling_map)

    metrics = {}
    metrics.update(compute_shortest_path_metrics(G))
    metrics.update(compute_clustering_and_assortativity(G))
    metrics.update(compute_edge_betweenness_and_spectral_gap(G))

    return metrics

def load_raw_snapshots(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Load all raw JSON snapshots from the data/raw directory.
    Returns a list of dicts containing device_id, timestamp, and coupling_map.
    """
    snapshots = []
    path = Path(raw_dir)
    if not path.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist.")
        return snapshots

    for file_path in path.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Extract device_id from filename or content
            device_id = data.get('device_id', file_path.stem.split('_')[0])
            timestamp = data.get('timestamp', datetime.now().isoformat())
            coupling_map = data.get('coupling_map', [])

            if not isinstance(coupling_map, list):
                logger.warning(f"Invalid coupling_map in {file_path}")
                continue

            snapshots.append({
                "device_id": device_id,
                "timestamp": timestamp,
                "coupling_map": coupling_map,
                "source_file": str(file_path)
            })
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {file_path}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    return snapshots

def generate_graph_metrics_csv(raw_dir: str, output_path: str) -> None:
    """
    Generate data/processed/graph_metrics.csv.
    Reads raw JSON snapshots, computes metrics, and writes to CSV.
    Columns: device_id, metric_name, value, is_finite
    """
    snapshots = load_raw_snapshots(raw_dir)

    if not snapshots:
        logger.error("No raw snapshots found. Cannot generate graph metrics.")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for snap in snapshots:
        device_id = snap['device_id']
        coupling_map = snap['coupling_map']
        metrics = process_device_coupling_map(coupling_map)

        for metric_name, value in metrics.items():
            is_finite = bool(np.isfinite(value))
            rows.append({
                "device_id": device_id,
                "metric_name": metric_name,
                "value": value,
                "is_finite": is_finite
            })

    with open(output_file, 'w', newline='') as f:
        fieldnames = ["device_id", "metric_name", "value", "is_finite"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} graph metrics to {output_path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate graph metrics CSV from raw snapshots")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Path to raw data directory")
    # Support both --output and legacy --out flags
    parser.add_argument("--output", type=str, default="data/processed/graph_metrics.csv",
                        help="Output CSV path")
    parser.add_argument("--out", type=str, help="Alias for --output (legacy flag)")

    parser.add_argument("--generate-metrics", action="store_true",
                        help="Legacy flag to trigger metric generation")

    args = parser.parse_args()

    # Resolve output path, giving precedence to --out if supplied
    output_path = args.out if args.out is not None else args.output

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run generation (the flag is kept for backward compatibility)
    if args.generate_metrics or not args.generate_metrics:
        generate_graph_metrics_csv(args.raw_dir, output_path)

if __name__ == "__main__":
    main()
