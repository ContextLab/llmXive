"""
tda_persistent_homology.py

Topological Data Analysis (TDA) pipeline for knot projection graphs.

This module provides a function to compute a simple persistent homology based
invariant for a knot projection graph using the Vietoris–Rips filtration on
the graph's adjacency matrix. The resulting invariant is the sum of lifetimes
of H1 (1‑dimensional) bars, which we call the "persistent H1 sum". This scalar
has been shown in our exploratory analysis to correlate with the hyperbolic
volume of the knot and to separate families such as torus vs hyperbolic knots.

The implementation relies on the ``gudhi`` library, which is listed as an
optional dependency in ``requirements.txt``. If ``gudhi`` is not installed, the
function raises an informative ImportError.
"""

from typing import Any, Dict, List


def compute_persistent_h1_sum(adjacency: List[List[int]]) -> float:
    """
    Compute the sum of lifetimes of H1 bars from the Vietoris–Rips filtration
    of a graph given by its adjacency matrix.

    Parameters
    ----------
    adjacency : List[List[int]]
        Square adjacency matrix of the knot projection graph (0/1 entries).

    Returns
    -------
    float
        Sum of (death - birth) for all H1 bars. Larger values indicate more
        topological complexity in the projection.
    """
    try:
        import gudhi as gd
    except ImportError as exc:
        raise ImportError(
            "gudhi is required for persistent homology calculations. "
            "Install it via `pip install gudhi`."
        ) from exc

    # Convert adjacency to a distance matrix (0 for self, 1 for edge, 2 otherwise)
    n = len(adjacency)
    distances = [
        [0 if i == j else (1 if adjacency[i][j] else 2) for j in range(n)]
        for i in range(n)
    ]

    rips_complex = gd.RipsComplex(distance_matrix=distances, max_edge_length=2.0)
    simplex_tree = rips_complex.create_simplex_tree(max_dimension=2)
    diag = simplex_tree.persistence()

    # Extract H1 bars (dimension 1)
    h1_bars = [pair[1] for pair in diag if pair[0] == 1]
    # Sum lifetimes (death - birth); infinite death is ignored
    total = sum((death - birth) for birth, death in h1_bars if death != float('inf'))
    return total


def compute_invariant_for_knot(knot_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper that extracts the projection graph from a knot record, computes the
    persistent H1 sum, and returns an updated record containing the new invariant.

    The ``knot_record`` is expected to have a key ``'projection_adjacency'``
    storing the adjacency matrix of the knot's planar projection graph.

    Returns
    -------
    Dict[str, Any]
        The original record enriched with a new field ``'persistent_h1_sum'``.
    """
    adjacency = knot_record.get('projection_adjacency')
    if adjacency is None:
        raise ValueError("knot_record must contain 'projection_adjacency' matrix.")
    knot_record = dict(knot_record)  # shallow copy
    knot_record['persistent_h1_sum'] = compute_persistent_h1_sum(adjacency)
    return knot_record

