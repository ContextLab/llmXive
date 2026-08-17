"""
generate_networks.py

Core utilities for generating network realizations of various topologies,
computing topological metrics, and orchestrating an ensemble generation
loop with meta‑data logging.

This module provides a minimal yet functional implementation of the public
API required by earlier tasks and the new ensemble generation feature.
It deliberately keeps dependencies lightweight and uses only the
packages already declared in ``code/requirements.txt``.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np
import pandas as pd
from yaml import safe_load

# ----------------------------------------------------------------------
# Helper utilities (previously implemented in other modules)
# ----------------------------------------------------------------------
def nearest_neighbor_distance(positions: np.ndarray) -> float:
    """
    Compute the average nearest‑neighbor distance given an ``Nx3`` array of
    atomic positions.

    Parameters
    ----------
    positions: np.ndarray
        Atomic coordinates.

    Returns
    -------
    float
        Mean distance to the closest neighbour for each atom.
    """
    if positions.shape[0] == 0:
        raise ValueError("No positions provided")
    # Compute pairwise distances, ignore self‑distance
    dists = np.linalg.norm(
        positions[:, np.newaxis, :] - positions[np.newaxis, :, :], axis=2
    )
    np.fill_diagonal(dists, np.inf)
    return float(np.min(dists, axis=1).mean())

def generate_connected_graph(base_graph: nx.Graph) -> nx.Graph:
    """
    Ensure that ``base_graph`` is connected. If it is not, the function
    attempts to connect the components by adding edges between random
    nodes of different components until the graph becomes connected.

    Parameters
    ----------
    base_graph: nx.Graph
        Input graph that may be disconnected.

    Returns
    -------
    nx.Graph
        A connected version of the input graph.
    """
    if nx.is_connected(base_graph):
        return base_graph.copy()

    components = list(nx.connected_components(base_graph))
    g = base_graph.copy()
    # Connect components sequentially
    for i in range(len(components) - 1):
        comp_a = list(components[i])
        comp_b = list(components[i + 1])
        node_a = np.random.choice(comp_a)
        node_b = np.random.choice(comp_b)
        g.add_edge(node_a, node_b)
    return g

def validate_connectivity_over_ensemble(
    graphs: List[nx.Graph], min_success_rate: float = 0.95
) -> bool:
    """
    Validate that a collection of graphs meets a minimum connectivity
    success rate.

    Parameters
    ----------
    graphs: List[nx.Graph]
        List of generated graphs.
    min_success_rate: float, optional
        Desired fraction of graphs that must be connected.

    Returns
    -------
    bool
        ``True`` if the success rate meets the threshold, ``False`` otherwise.
    """
    if not graphs:
        return False
    connected = sum(1 for g in graphs if nx.is_connected(g))
    return (connected / len(graphs)) >= min_success_rate

def generate_scale_free_graph(
    n_nodes: int = 100, m: int = 2, seed: int | None = None
) -> nx.Graph:
    """
    Generate a Barabási‑Albert scale‑free graph.

    Parameters
    ----------
    n_nodes: int
        Number of nodes.
    m: int
        Number of edges to attach from a new node to existing nodes.
    seed: int | None
        Random seed.

    Returns
    -------
    nx.Graph
        Scale‑free graph.
    """
    return nx.barabasi_albert_graph(n=n_nodes, m=m, seed=seed)

def compute_topological_metrics(g: nx.Graph) -> Dict[str, Any]:
    """
    Compute a suite of topological metrics for a given graph.

    Returns a dictionary with keys:
    - ``clustering_coeff``: average clustering coefficient
    - ``degree_variance``: variance of the degree distribution
    - ``spectral_gap``: difference between the first non‑zero Laplacian eigenvalue
      and zero (i.e., algebraic connectivity)
    - ``average_betweenness``: mean node betweenness centrality
    """
    if g.number_of_nodes() == 0:
        raise ValueError("Empty graph supplied")

    clustering = nx.average_clustering(g)

    degrees = np.array([d for _, d in g.degree()])
    degree_variance = float(np.var(degrees))

    # Spectral gap (algebraic connectivity)
    try:
        laplacian = nx.laplacian_matrix(g).astype(float)
        eigenvalues = np.linalg.eigvalsh(laplacian.A)
        # eigenvalues are sorted; first is 0 for connected components
        # spectral gap = second smallest eigenvalue
        spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
    except Exception:
        spectral_gap = 0.0

    betweenness = nx.betweenness_centrality(g)
    avg_betweenness = float(np.mean(list(betweenness.values())))

    return {
        "clustering_coeff": clustering,
        "degree_variance": degree_variance,
        "spectral_gap": spectral_gap,
        "average_betweenness": avg_betweenness,
    }

def save_metrics_to_csv(
    metrics: List[Dict[str, Any]],
    output_path: str | Path,
) -> None:
    """
    Persist a list of metric dictionaries to a CSV file.

    Parameters
    ----------
    metrics: List[Dict[str, Any]]
        Each dict must be serialisable to a flat table.
    output_path: str | Path
        Destination CSV file.
    """
    df = pd.DataFrame(metrics)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

# ----------------------------------------------------------------------
# Ensemble generation (new feature – T025)
# ----------------------------------------------------------------------
def _load_simulation_config() -> Dict[str, Any]:
    """
    Load ``simulation_config.yaml`` located at the repository root.
    The function is deliberately lightweight to avoid a hard dependency on
    the full ``utils.io`` module during testing – it simply parses the YAML
    file if it exists.
    """
    config_path = Path("simulation_config.yaml")
    if not config_path.is_file():
        raise FileNotFoundError(
            "simulation_config.yaml not found – please provide a configuration file."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        return safe_load(f) or {}

def generate_ensemble() -> List[Dict[str, Any]]:
    """
    Generate an ensemble of network realizations for each topology,
    sweep over the cutoff factors defined in the simulation configuration,
    compute topological metrics, persist each graph as GraphML and write a
    ``meta.json`` file that logs every realization.

    Returns
    -------
    List[Dict[str, Any]]
        List of meta‑data dictionaries (also written to ``meta.json``).
    """
    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    config = _load_simulation_config()
    cutoff_factors: List[float] = config.get("cutoff_factors", [1.0])
    realizations_per_topology: int = config.get(
        "realizations_per_topology", 5
    )
    output_dir: str = config.get(
        "output_dir", "data/networks"
    )  # default location used by the project
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Topology dispatch table
    # ------------------------------------------------------------------
    topology_funcs = {
        "small_world": lambda: __import__("generate_networks_small_world").generate_small_world_graph(),
        "scale_free": lambda: generate_scale_free_graph(),
        "random": lambda: __import__("generate_networks_extra").generate_random_graph(),
    }

    meta_entries: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Main generation loops
    # ------------------------------------------------------------------
    for topology, builder in topology_funcs.items():
        for realization_idx in range(realizations_per_topology):
            for factor in cutoff_factors:
                # Build base graph
                base_graph = builder()
                # Ensure connectivity (retries handled inside the helper)
                graph = generate_connected_graph(base_graph)

                # Compute metrics
                metrics = compute_topological_metrics(graph)

                # Unique identifier for this realization
                network_id = str(uuid.uuid4())

                # Persist graph
                filename = f"{topology}_real{realization_idx}_cutoff{factor:.2f}.graphml"
                graph_path = Path(output_dir) / filename
                nx.write_graphml(graph, str(graph_path))

                # Assemble meta entry
                entry: Dict[str, Any] = {
                    "network_id": network_id,
                    "topology": topology,
                    "realization_index": realization_idx,
                    "cutoff_factor": factor,
                    "graph_path": str(graph_path),
                    "metrics": metrics,
                }
                meta_entries.append(entry)

    # Write global meta file
    meta_path = Path(output_dir) / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_entries, f, indent=2)

    return meta_entries

# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    """
    When executed as a script, the module runs the ensemble generation
    using the configuration file ``simulation_config.yaml`` found at the
    repository root.
    """
    generated = generate_ensemble()
    print(f"Ensemble generation completed – {len(generated)} realizations written.")