"""Composite metric based on weighted Shannon entropy.

This module implements a novel composite metric that synthesises the classic
invariants *crossing number* and *braid index* into a single descriptor.  The
metric treats the distribution of crossing types (e.g. positive vs. negative
crossings) as a probability distribution, computes its Shannon entropy, and
weights the resulting entropy by the braid index.  The resulting value captures
both the combinatorial complexity of the diagram (through entropy) and its
topological depth (through the braid index), offering a richer signal than the
raw tuple ``(crossing_number, braid_index)``.

The implementation is deliberately lightweight and does not depend on any
external scientific libraries – only the Python standard library.  It can be
used directly in the analysis pipeline or as a feature for downstream machine
learning models (e.g. graph‑neural‑network embeddings).
"""

from __future__ import annotations

import math
from typing import Dict, Iterable


def _shannon_entropy(probabilities: Iterable[float]) -> float:
    """Return the Shannon entropy (base‑2) of a probability distribution.

    Parameters
    ----------
    probabilities: iterable of float
        Probabilities that sum to 1. Zero probabilities are ignored.
    """
    return -sum(p * math.log(p, 2) for p in probabilities if p > 0)


def weighted_entropy_metric(crossing_counts: Dict[str, int], braid_index: int) -> float:
    """Compute the weighted entropy composite metric.

    The metric is defined as ``entropy * braid_index`` where ``entropy`` is the
    Shannon entropy of the normalized crossing‑type distribution.

    Parameters
    ----------
    crossing_counts: dict
        Mapping from crossing type (e.g. ``"positive"``, ``"negative"``) to its
        observed count in the knot diagram.
    braid_index: int
        The braid index of the knot diagram.

    Returns
    -------
    float
        The weighted entropy value.  Returns ``0.0`` when there are no crossings.
    """
    total = sum(crossing_counts.values())
    if total == 0:
        return 0.0
    probabilities = [count / total for count in crossing_counts.values()]
    entropy = _shannon_entropy(probabilities)
    return entropy * braid_index


def compute_metric_from_diagram(diagram: Dict) -> float:
    """Convenience wrapper that extracts the necessary information from a diagram.

    The expected ``diagram`` dictionary should contain:

    * ``"crossings"`` – an iterable of crossing descriptors where each element has
      a ``"type"`` field (e.g. ``"positive"`` or ``"negative"``).
    * ``"braid_index"`` – an integer representing the braid index.

    Example
    -------
    >>> diagram = {
    ...     "crossings": [{"type": "positive"}, {"type": "negative"}, {"type": "positive"}],
    ...     "braid_index": 4,
    ... }
    >>> weighted_entropy_metric({"positive": 2, "negative": 1}, 4)
    2.0
    """
    crossings = diagram.get("crossings", [])
    braid_index = diagram.get("braid_index", 0)
    # Count crossing types
    crossing_counts: Dict[str, int] = {}
    for crossing in crossings:
        ctype = crossing.get("type", "unknown")
        crossing_counts[ctype] = crossing_counts.get(ctype, 0) + 1
    return weighted_entropy_metric(crossing_counts, braid_index)


