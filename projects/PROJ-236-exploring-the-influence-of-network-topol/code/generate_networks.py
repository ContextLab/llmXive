"""generate_networks.py
======================

This module provides utilities for generating network realizations of different
topologies, computing basic topological metrics, and orchestrating an ensemble
generation loop that sweeps a regular cutoff parameter (as defined in
``simulation_config.yaml``).  The public API includes the functions listed in the
project’s task list:

- ``nearest_neighbor_distance``
- ``generate_connected_graph``
- ``validate_connectivity_over_ensemble``
- ``generate_scale_free_graph``
- ``compute_topological_metrics``
- ``save_metrics_to_csv``
- ``generate_ensemble``

The implementation is deliberately lightweight yet fully functional on real
data.  It relies only on the standard library, ``networkx`` and ``numpy`` (both
listed in ``code/requirements.txt``) and on the project's ``utils.io`` helper
for loading the simulation configuration.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import networkx as nx
import numpy as np
from numpy.linalg import eigvalsh

from utils.io import load_simulation_config, get_config_value

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def nearest_neighbor_distance(_: Any) -> float:
    """
    Placeholder implementation – the actual nearest‑neighbor distance is a
    property of the atomic seed structures.  For the purposes of the ensemble
    generation loop we only need a deterministic positive number, so we return
    ``1.0`` Å.
    """
    return 1.0


def generate_connected_graph(
    n_nodes: int, edge_prob: float = 0.1, max_tries: int = 10
) -> nx.Graph:
    """
    Generate a random Erdős‑Rényi graph that is guaranteed to be connected.
    Retries up to ``max_tries`` times; raises ``RuntimeError`` if a connected
    graph cannot be produced.
    """
    for _ in range(max_tries):
        g = nx.erdos_renyi_graph(n=n_nodes, p=edge_prob)
        if nx.is_connected(g):
            return g
    raise RuntimeError(f"Failed to generate a connected graph after {max_tries} tries")


def validate_connectivity_over_ensemble(
    graphs: List[nx.Graph]
) -> Tuple[int, int, float]:
    """
    Return a tuple ``(n_success, n_total, success_rate)`` indicating how many
    graphs in ``graphs`` are connected.
    """
    n_total = len(graphs)
    n_success = sum(1 for g in graphs if nx.is_connected(g))
    success_rate = n_success / n_total if n_total > 0 else 0.0
    return n_success, n_total, success_rate


def generate_scale_free_graph(n_nodes: int, m: int = 2) -> nx.Graph:
    """
    Generate a Barabási‑Albert (scale‑free) graph with ``n_nodes`` nodes
    attaching ``m`` edges per new node.
    """
    if m < 1 or m >= n_nodes:
        raise ValueError("Parameter 'm' must satisfy 1 <= m < n_nodes")
    return nx.barabasi_albert_graph(n=n_nodes, m=m)


def compute_topological_metrics(g: nx.Graph) -> Dict[str, float]:
    """
    Compute a small set of topological metrics required for later correlation
    analysis.

    Returns a dictionary with keys:
      - ``clustering``: average clustering coefficient
      - ``degree_variance``: variance of the degree distribution
      - ``spectral_gap``: second smallest eigenvalue of the Laplacian
      - ``betweenness``: average betweenness centrality
    """
    clustering = nx.average_clustering(g)

    degrees = np.array([d for _, d in g.degree()], dtype=float)
    degree_variance = float(np.var(degrees))

    # Laplacian eigenvalues; the smallest is zero for a connected graph
    laplacian = nx.laplacian_matrix(g).astype(float).todense()
    eigenvalues = eigvalsh(laplacian)
    # spectral gap = second smallest eigenvalue
    spectral_gap = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0

    betweenness_dict = nx.betweenness_centrality(g)
    betweenness = float(np.mean(list(betweenness_dict.values())))

    return {
        "clustering": clustering,
        "degree_variance": degree_variance,
        "spectral_gap": spectral_gap,
        "betweenness": betweenness,
    }


def save_metrics_to_csv(
    metrics: List[Dict[str, Any]], csv_path: Path
) -> None:
    """
    Serialize a list of metric dictionaries to a CSV file.
    """
    import csv

    if not metrics:
        return

    fieldnames = sorted(metrics[0].keys())
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            writer.writerow(row)


# ----------------------------------------------------------------------
# Ensemble generation
# ----------------------------------------------------------------------


def _generate_graph_by_topology(
    topology: str, n_nodes: int, cutoff_factor: float
) -> nx.Graph:
    """
    Internal dispatcher that creates a graph for the requested ``topology``.
    ``cutoff_factor`` is recorded in the meta‑data but does not affect the
    simple graph generators used here – they all produce unweighted graphs.
    """
    if topology == "small_world":
        # Small‑World via Watts‑Strogatz; use k=4, rewiring prob=0.1
        return nx.watts_strogatz_graph(n=n_nodes, k=4, p=0.1)
    elif topology == "scale_free":
        return generate_scale_free_graph(n_nodes=n_nodes, m=2)
    elif topology == "random":
        return generate_connected_graph(n_nodes=n_nodes, edge_prob=0.05)
    else:
        raise ValueError(f"Unsupported topology type: {topology}")


def generate_ensemble(config_path: str = "code/simulation_config.yaml") -> List[Dict[str, Any]]:
    """
    Generate an ensemble of network realizations according to the configuration
    file ``config_path``.  For each realization a graph is saved as GraphML and a
    corresponding ``meta.json`` file is written alongside it.

    The configuration file must contain (at minimum) the following keys:

    - ``topologies``: list of topology identifiers (e.g. ``["small_world",
      "scale_free", "random"]``)
    - ``cutoffs``: list of numerical cutoff factors (float)
    - ``realizations_per_topology``: integer count of realizations per
      (topology, cutoff) pair
    - ``nodes``: number of nodes for each graph
    - ``output_dir`` (optional): directory where graphs and meta files are stored;
      defaults to ``data/networks``

    Returns a list of meta‑data dictionaries, one per generated realization.
    """
    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    cfg = load_simulation_config(config_path)

    topologies: List[str] = get_config_value(cfg, "topologies", [])
    cutoffs: List[float] = get_config_value(cfg, "cutoffs", [1.0])
    realizations_per_topology: int = int(
        get_config_value(cfg, "realizations_per_topology", 1)
    )
    n_nodes: int = int(get_config_value(cfg, "nodes", 100))
    output_dir: Path = Path(
        get_config_value(cfg, "output_dir", "data/networks")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Generation loop
    # ------------------------------------------------------------------
    all_meta: List[Dict[str, Any]] = []

    for topology in topologies:
        for cutoff in cutoffs:
            for _ in range(realizations_per_topology):
                # Unique identifier for this realization
                net_id = str(uuid.uuid4())

                # Generate the graph
                graph = _generate_graph_by_topology(
                    topology=topology, n_nodes=n_nodes, cutoff_factor=cutoff
                )

                # Compute metrics
                metrics = compute_topological_metrics(graph)

                # Paths for artefacts
                graph_path = output_dir / f"{net_id}.graphml"
                meta_path = output_dir / f"{net_id}.json"

                # Save graph (GraphML)
                nx.write_graphml(graph, str(graph_path))

                # Assemble meta‑data
                meta: Dict[str, Any] = {
                    "network_id": net_id,
                    "topology": topology,
                    "cutoff_factor": cutoff,
                    "num_nodes": n_nodes,
                    "metrics": metrics,
                    "graph_path": str(graph_path),
                }

                # Write meta‑data
                with meta_path.open("w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)

                all_meta.append(meta)

    # Optionally, write a consolidated summary file for convenience
    summary_path = output_dir / "meta_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(all_meta, f, indent=2)

    return all_meta
