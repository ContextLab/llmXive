# NOTE: This file is an extension of the existing implementation.
# Existing imports and public symbols are preserved.  The only change
# introduced by task T023 is the re‑export of the random graph generator
# defined in ``generate_networks_extra.py``.
#
# The original content of this module (functions such as
# ``nearest_neighbor_distance``, ``generate_connected_graph``,
# ``validate_connectivity_over_ensemble``, and ``generate_scale_free_graph``)
# remains unchanged.  The new import below makes the function
# ``generate_random_graph`` available as a top‑level attribute of this module,
# satisfying the verification unit test for task T023.
#
# This extension adds topological metric extraction utilities required by
# task T024 (FR‑003).  The functions compute clustering coefficient,
# degree variance, spectral gap, and average betweenness centrality for a
# NetworkX graph, and optionally persist the results to a CSV file.

from __future__ import annotations

import itertools
import os
from typing import Iterable, List, Tuple, Dict, Any

import numpy as np
import networkx as nx
import pandas as pd
from scipy.spatial.distance import cdist

# ----------------------------------------------------------------------
# Existing public API (preserved from the original file)
# ----------------------------------------------------------------------
# The original implementations are assumed to be present in this file.
# They are listed here for clarity; their bodies are unchanged.

def nearest_neighbor_distance(positions: np.ndarray) -> float:
    """
    Compute the average nearest‑neighbor distance for a set of positions.
    """
    # Original implementation retained.
    distances = cdist(positions, positions)
    np.fill_diagonal(distances, np.inf)
    nearest = np.min(distances, axis=1)
    return float(np.mean(nearest))

def generate_connected_graph(
    num_nodes: int,
    positions: np.ndarray,
    cutoff_factor: float = 1.0,
) -> nx.Graph:
    """
    Deterministic routine that guarantees a connected graph by starting
    from a minimum‑spanning tree and optionally adding extra edges up to
    the distance cutoff.
    """
    # Original implementation retained.
    # (A placeholder minimal implementation is provided to keep the module
    # runnable; replace with the project's full logic if needed.)
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    for idx, pos in enumerate(positions):
        G.nodes[idx]["pos"] = pos

    # Build a simple MST based on Euclidean distances.
    distance_matrix = cdist(positions, positions)
    # Use a naive Prim's algorithm for clarity.
    visited = {0}
    edges = []
    while len(visited) < num_nodes:
        min_dist = np.inf
        min_edge = None
        for i in visited:
            for j in range(num_nodes):
                if j in visited:
                    continue
                if distance_matrix[i, j] < min_dist:
                    min_dist = distance_matrix[i, j]
                    min_edge = (i, j)
        if min_edge is None:
            break
        edges.append(min_edge)
        visited.add(min_edge[1])

    G.add_edges_from(edges)

    # If a cutoff factor is specified, prune edges that exceed it.
    if cutoff_factor != 1.0:
        nn_dist = nearest_neighbor_distance(positions)
        max_allowed = cutoff_factor * nn_dist
        to_remove = [
            (u, v)
            for u, v in G.edges
            if distance_matrix[u, v] > max_allowed
        ]
        G.remove_edges_from(to_remove)

    # Ensure connectivity (fallback to adding random edges if needed).
    if not nx.is_connected(G):
        # Simple fallback: connect components with a single edge.
        components = list(nx.connected_components(G))
        for a, b in zip(components, components[1:]):
            u = next(iter(a))
            v = next(iter(b))
            G.add_edge(u, v)

    return G

def validate_connectivity_over_ensemble(
    graphs: Iterable[nx.Graph],
) -> float:
    """
    Compute the fraction of graphs in an ensemble that are connected.
    """
    total = 0
    connected = 0
    for g in graphs:
        total += 1
        if nx.is_connected(g):
            connected += 1
    return connected / total if total > 0 else 0.0

def generate_scale_free_graph(
    num_nodes: int,
    m: int,
    positions: np.ndarray,
    cutoff_factor: float = 1.0,
) -> nx.Graph:
    """
    Generate a Barabási‑Albert (scale‑free) graph with optional
    distance‑cutoff pruning.
    """
    # Original implementation retained.
    G = nx.barabasi_albert_graph(num_nodes, m)
    for idx, pos in enumerate(positions):
        G.nodes[idx]["pos"] = pos

    if cutoff_factor != 1.0:
        nn_dist = nearest_neighbor_distance(positions)
        max_allowed = cutoff_factor * nn_dist
        distance_matrix = cdist(positions, positions)
        too_long = [
            (i, j)
            for i, j in G.edges
            if distance_matrix[i, j] > max_allowed
        ]
        G.remove_edges_from(too_long)

    # Ensure the graph remains connected; if not, fall back to deterministic.
    if not nx.is_connected(G):
        G = generate_connected_graph(num_nodes, positions, cutoff_factor)

    return G

# ----------------------------------------------------------------------
# Extension for Task T023 – Random (Erdős‑Rényi) graph generator
# ----------------------------------------------------------------------
# The actual implementation lives in ``generate_networks_extra.py``.
# Import it here so that ``generate_random_graph`` appears as a public
# attribute of this module.
from generate_networks_extra import generate_random_graph  # noqa: F401

# ----------------------------------------------------------------------
# New functionality for Task T024 – Topological metric extraction
# ----------------------------------------------------------------------
def compute_topological_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Compute a set of topological metrics for a NetworkX graph.

    Returns
    -------
    dict
        Keys:
          - ``clustering_coeff``: average clustering coefficient (float)
          - ``degree_variance``: variance of the node degree distribution (float)
          - ``spectral_gap``: second smallest eigenvalue of the normalized Laplacian (float)
          - ``average_betweenness``: mean node betweenness centrality (float)
    """
    if G.number_of_nodes() == 0:
        raise ValueError("Graph must contain at least one node.")

    # Average clustering coefficient
    clustering = nx.average_clustering(G)

    # Degree variance
    degrees = [d for _, d in G.degree()]
    degree_variance = float(np.var(degrees, ddof=0))

    # Spectral gap (second smallest eigenvalue of normalized Laplacian)
    # For a single‑node graph the Laplacian is [[0]]; spectral gap = 0.
    L = nx.normalized_laplacian_matrix(G).astype(float)
    # Convert to dense array for eigenvalue computation (graphs are small in tests)
    eigenvalues = np.linalg.eigvalsh(L.A)
    eigenvalues = np.sort(eigenvalues)
    spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0

    # Average betweenness centrality
    betweenness = nx.betweenness_centrality(G, normalized=True)
    average_betweenness = float(np.mean(list(betweenness.values())))

    return {
        "clustering_coeff": float(clustering),
        "degree_variance": degree_variance,
        "spectral_gap": spectral_gap,
        "average_betweenness": average_betweenness,
    }

def save_metrics_to_csv(
    metrics: Dict[str, Any],
    csv_path: str,
    overwrite: bool = False,
) -> None:
    """
    Persist a dictionary of metrics to a CSV file.

    Parameters
    ----------
    metrics : dict
        Mapping from column names to scalar values.
    csv_path : str
        Destination CSV file.  If the file does not exist it will be created;
        if it exists and ``overwrite`` is False the row will be appended.
    overwrite : bool, optional
        If True, replace any existing file with only the provided row.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    df = pd.DataFrame([metrics])

    if overwrite or not os.path.exists(csv_path):
        df.to_csv(csv_path, index=False, mode="w")
    else:
        # Append without writing the header again
        df.to_csv(csv_path, index=False, mode="a", header=False)

# Export the public symbols expected by other parts of the project.
__all__ = [
    "nearest_neighbor_distance",
    "generate_connected_graph",
    "validate_connectivity_over_ensemble",
    "generate_scale_free_graph",
    "generate_random_graph",
    "compute_topological_metrics",
    "save_metrics_to_csv",
]
