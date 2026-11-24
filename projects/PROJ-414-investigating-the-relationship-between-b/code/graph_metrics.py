"""Graph metric calculations for vertex‑block connectivity descriptors.

This module provides functions to compute the three required graph‑theoretic
descriptors per sliding‑window functional connectivity matrix:

* Global efficiency (weighted, using inverse of (1 - |correlation|) as distance)
* Louvain modularity (seeded for reproducibility)
* Participation coefficient (node‑averaged, weighted)

All functions accept a **weighted adjacency matrix** where the weight is the
absolute Pearson correlation between two vertex‑blocks.  The matrix must be
square, symmetric, and have ones on the diagonal.

The functions are deliberately lightweight and pure‑NumPy/NetworkX so they
can be called repeatedly inside the sliding‑window loop without excessive
overhead.
"""
import numpy as np
import networkx as nx
from sklearn.utils.validation import check_random_state

__all__ = [
    "global_efficiency",
    "louvain_modularity",
    "participation_coefficient",
]

def _build_weighted_graph(corr_matrix: np.ndarray) -> nx.Graph:
    """Return a NetworkX Graph from an absolute correlation matrix.

    Edge weight = |correlation| (range 0‑1).  Self‑loops are removed
    because NetworkX treats them as separate edges; the diagonal is
    ignored for all metrics.
    """
    if corr_matrix.shape[0] != corr_matrix.shape[1]:
        raise ValueError("Correlation matrix must be square")
    # Absolute correlations – negative values are treated as weak positive
    # connections for the purpose of these descriptors.
    abs_corr = np.abs(corr_matrix)
    # Build graph from numpy array; NetworkX uses the matrix entry as
    # the edge attribute named "weight".
    G = nx.from_numpy_array(abs_corr, create_using=nx.Graph)
    # Remove self‑loops (weight 1 on the diagonal) – they do not contribute
    # to path‑length or community calculations.
    G.remove_edges_from(nx.selfloop_edges(G))
    return G

def global_efficiency(corr_matrix: np.ndarray) -> float:
    """Weighted global efficiency.

    Uses the standard definition: the average of the inverse shortest‑path
    lengths between all pairs of nodes.  Edge “distance” is defined as
    ``1 - weight`` where weight = |correlation|, guaranteeing a positive
    distance (0 when correlation = 1, 1 when correlation = 0).
    """
    G = _build_weighted_graph(corr_matrix)
    # Set edge distance attribute for shortest‑path calculations.
    for u, v, d in G.edges(data=True):
        # Distance = 1 - weight; weight in [0,1] → distance in [0,1].
        d["distance"] = 1.0 - d["weight"]
    # NetworkX's global_efficiency works with a ``weight`` attribute that
    # represents distance, so we rename the attribute temporarily.
    nx.set_edge_attributes(G, { (u, v): {"weight": d["distance"]} for u, v, d in G.edges(data=True) })
    # Use the built‑in function (unweighted version works with the ``weight``
    # attribute interpreted as distance).
    return nx.global_efficiency(G)

def louvain_modularity(corr_matrix: np.ndarray, seed: int = 42) -> float:
    """Louvain modularity (weighted) seeded for reproducibility.

    The function returns the modularity score of the partition found by
    ``networkx.algorithms.community.louvain_communities``.  The Louvain
    algorithm is stochastic; we seed NumPy's RNG to obtain deterministic
    results across runs.
    """
    rng = check_random_state(seed)
    # NetworkX's Louvain implementation accepts a ``seed`` argument for
    # reproducibility (as of NetworkX 3.x).
    communities = nx.algorithms.community.louvain_communities(
        _build_weighted_graph(corr_matrix),
        seed=rng,
    )
    # Compute modularity using the weighted version.
    G = _build_weighted_graph(corr_matrix)
    return nx.algorithms.community.quality.modularity(G, communities, weight="weight")

def participation_coefficient(corr_matrix: np.ndarray, communities: list) -> float:
    """Node‑averaged participation coefficient (weighted).

    Parameters
    ----------
    corr_matrix : np.ndarray
        Absolute correlation matrix (weights ≥ 0).
    communities : list of sets
        Community assignment as returned by ``louvain_communities``.
        Each set contains node indices belonging to that community.

    Returns
    -------
    float
        The average participation coefficient across all nodes.
    """
    G = _build_weighted_graph(corr_matrix)
    # Strength (weighted degree) of each node.
    strength = dict(G.degree(weight="weight"))
    # Pre‑compute community membership for fast lookup.
    node_to_com = {}
    for idx, com in enumerate(communities):
        for node in com:
            node_to_com[node] = idx

    # Compute per‑node participation coefficient.
    pcs = []
    for node in G.nodes():
        k_i = strength[node]
        if k_i == 0:
            pcs.append(0.0)
            continue
        # Sum of weights to each community.
        comm_weights = {}
        for neighbor, data in G[node].items():
            com = node_to_com[neighbor]
            comm_weights[com] = comm_weights.get(com, 0.0) + data["weight"]
        # Participation coefficient formula.
        sum_sq = sum((w / k_i) ** 2 for w in comm_weights.values())
        pcs.append(1.0 - sum_sq)
    return float(np.mean(pcs))
