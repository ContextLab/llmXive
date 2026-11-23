"""
utils.convergence
------------------

Helper utilities for detecting convergence in the Hegselmann‑Krause (HK)
bounded‑confidence opinion dynamics model.

The module provides two public functions:

* ``has_converged(prev, cur, tol)`` – Returns ``True`` when the maximum
  absolute change between two opinion vectors is smaller than ``tol``.
* ``compute_clusters(opinions, epsilon)`` – Groups node identifiers into
  opinion clusters where all members of a cluster differ by at most
  ``epsilon``.  The function returns a list of lists of node identifiers.
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

def has_converged(prev: Sequence[float], cur: Sequence[float], tol: float = 1e-4) -> bool:
    """
    Determine whether the HK dynamics have converged.

    Parameters
    ----------
    prev : Sequence[float]
        Opinions from the previous iteration.
    cur : Sequence[float]
        Opinions from the current iteration.
    tol : float, optional
        Convergence tolerance; default is ``1e-4``.  Convergence is declared
        when ``max(|cur - prev|) < tol``.

    Returns
    -------
    bool
        ``True`` if converged, ``False`` otherwise.
    """
    prev_arr = np.asarray(prev, dtype=float)
    cur_arr = np.asarray(cur, dtype=float)
    if prev_arr.size == 0:
        return True
    max_change = np.max(np.abs(cur_arr - prev_arr))
    return max_change < tol


def compute_clusters(
    opinions: Sequence[float],
    epsilon: float,
    node_ids: Sequence[int] | None = None,
) -> List[List[int]]:
    """
    Compute opinion clusters given a confidence bound ``epsilon``.

    Two agents belong to the same cluster when the absolute difference of
    their final opinions does not exceed ``epsilon``.  The algorithm sorts
    agents by opinion and groups them greedily – this yields the same
    partition as the standard HK definition.

    Parameters
    ----------
    opinions : Sequence[float]
        Final opinions of the agents.
    epsilon : float
        Confidence bound used for clustering.
    node_ids : Sequence[int] | None, optional
        Identifiers of the agents. If ``None`` the agents are assumed to be
        labelled ``0 .. len(opinions)-1``.  The order of identifiers in the
        output respects the sorted opinion order.

    Returns
    -------
    List[List[int]]
        A list of clusters, each cluster being a list of node identifiers.
    """
    opinions_arr = np.asarray(opinions, dtype=float)
    if node_ids is None:
        node_ids = list(range(len(opinions_arr)))
    else:
        node_ids = list(node_ids)

    if len(opinions_arr) == 0:
        return []

    # Sort by opinion to make clustering deterministic
    sorted_idx = np.argsort(opinions_arr)
    sorted_ops = opinions_arr[sorted_idx]
    sorted_ids = [node_ids[i] for i in sorted_idx]

    clusters: List[List[int]] = []
    current_cluster: List[int] = [sorted_ids[0]]

    for i in range(1, len(sorted_ops)):
        if sorted_ops[i] - sorted_ops[i - 1] <= epsilon:
            current_cluster.append(sorted_ids[i])
        else:
            clusters.append(current_cluster)
            current_cluster = [sorted_ids[i]]
    clusters.append(current_cluster)
    return clusters