"""
Graph Builder utilities for converting IBM Quantum coupling maps into
undirected NetworkX graphs and extracting a suite of topological metrics.
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Core graph construction
# ----------------------------------------------------------------------
def build_coupling_graph(coupling_map: List[List[int]]) -> nx.Graph:
    """
    Build an undirected NetworkX graph from a coupling map.

    Parameters
    ----------
    coupling_map : list of [source, target] edges (directed list)

    Returns
    -------
    nx.Graph
        Undirected graph representing qubit connectivity.
    """
    G = nx.Graph()
    G.add_edges_from(coupling_map)  # NetworkX treats edges as undirected for Graph
    return G

def compute_shortest_path_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute average shortest‑path length and diameter for the largest
    connected component of ``G``.

    Returns
    -------
    dict
        Keys ``avg_shortest_path`` and ``diameter``.
    """
    if G.number_of_nodes() == 0:
        return {"avg_shortest_path": float("nan"), "diameter": float("nan")}

    # Use the largest connected component
    if not nx.is_connected(G):
        components = sorted(nx.connected_components(G), key=len, reverse=True)
        subgraph = G.subgraph(components[0])
    else:
        subgraph = G

    avg_path = nx.average_shortest_path_length(subgraph)
    diam = nx.diameter(subgraph)
    return {"avg_shortest_path": float(avg_path), "diameter": float(diam)}

def compute_clustering_and_assortativity(G: nx.Graph) -> Dict[str, float]:
    """
    Compute global clustering coefficient and degree assortativity.

    Returns
    -------
    dict
        Keys ``clustering_coeff`` and ``assortativity``.
    """
    clustering = nx.average_clustering(G)
    # NetworkX's degree_assortativity_coefficient returns NaN for tiny graphs;
    # we coerce NaN to 0.0 for consistency.
    assort = nx.degree_assortativity_coefficient(G)
    if np.isnan(assort):
        assort = 0.0
    return {"clustering_coeff": float(clustering), "assortativity": float(assort)}

def compute_edge_betweenness_and_spectral_gap(G: nx.Graph) -> Dict[str, float]:
    """
    Compute the mean edge betweenness centrality (unnormalized) and the
    spectral gap (algebraic connectivity) of the graph Laplacian.

    For disconnected graphs the spectral gap is defined as 0.0 (C‑002).

    Returns
    -------
    dict
        Keys ``edge_betweenness_mean`` and ``spectral_gap``.
    """
    if G.number_of_edges() == 0:
        betweenness_mean = 0.0
    else:
        # Use unnormalized betweenness so that each edge in a two‑node component
        # receives a value of 1.0, matching the unit test expectations.
        betweenness = nx.edge_betweenness_centrality(G, normalized=False)
        betweenness_mean = float(np.mean(list(betweenness.values())))

    # Spectral gap: second smallest eigenvalue of the Laplacian (algebraic connectivity)
    # For disconnected graphs this value is 0.0.
    if G.number_of_nodes() == 0:
        spectral_gap = 0.0
    else:
        laplacian = nx.laplacian_matrix(G).astype(float).todense()
        eigenvalues = np.linalg.eigvalsh(laplacian)
        eigenvalues = np.sort(eigenvalues)
        if len(eigenvalues) > 1:
            spectral_gap = float(eigenvalues[1])  # second smallest eigenvalue
        else:
            spectral_gap = 0.0

    return {"edge_betweenness_mean": betweenness_mean, "spectral_gap": spectral_gap}

# ----------------------------------------------------------------------
# Convenience wrappers for the CLI / batch processing
# ----------------------------------------------------------------------
def process_device_coupling_map(coupling_map: List[List[int]]) -> Dict[str, Any]:
    """
    Compute all graph metrics for a single device's coupling map.
    Returns a flat dictionary with metric names as keys.
    """
    G = build_coupling_graph(coupling_map)
    metrics = {}
    metrics.update(compute_shortest_path_metrics(G))
    metrics.update(compute_clustering_and_assortativity(G))
    metrics.update(compute_edge_betweenness_and_spectral_gap(G))
    return metrics

def load_raw_snapshots(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Load all raw JSON snapshots from ``raw_dir``.
    Returns a list of dictionaries containing at least ``device_id``,
    ``timestamp`` and ``coupling_map``.
    """
    snapshots = []
    for fname in os.listdir(raw_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(raw_dir, fname)
        with open(path, "r") as f:
            data = json.load(f)
            snapshots.append(
                {
                    "device_id": data.get("device_id"),
                    "timestamp": data.get("timestamp"),
                    "coupling_map": data.get("coupling_map", []),
                }
            )
    return snapshots

def generate_graph_metrics_csv(raw_dir: str, output_path: str) -> None:
    """
    Generate ``data/processed/graph_metrics.csv`` from raw snapshots.
    The CSV is in long format: device_id, metric_name, value, is_finite.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["device_id", "metric_name", "value", "is_finite"])

        for snap in load_raw_snapshots(raw_dir):
            device_id = snap["device_id"]
            coupling_map = snap.get("coupling_map", [])
            if not coupling_map:
                continue
            metrics = process_device_coupling_map(coupling_map)
            for name, val in metrics.items():
                writer.writerow([device_id, name, val, True])

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Command‑line interface for the graph builder.

    Usage examples:
    ``python -m code.graph_builder --raw-dir data/raw --out data/processed/graph_metrics.csv``
    """
    import argparse

    parser = argparse.ArgumentParser(description="Build coupling graphs and compute metrics.")
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Directory containing raw JSON snapshots (default: data/raw)",
    )
    parser.add_argument(
        "--output",
        dest="out",
        help="Path to write the CSV of graph metrics (legacy flag).",
    )
    parser.add_argument(
        "--out",
        help="Path to write the CSV of graph metrics (preferred flag).",
    )
    parser.add_argument(
        "--generate-metrics",
        action="store_true",
        help="If set, the script will generate the CSV immediately.",
    )
    args = parser.parse_args()

    out_path = args.out or args.out  # handle both flags
    if not out_path:
        parser.error("Either --out or --output must be specified.")

    if args.generate_metrics:
        generate_graph_metrics_csv(args.raw_dir, out_path)
        logger.info(f"Graph metrics written to {out_path}")

if __name__ == "__main__":
    main()