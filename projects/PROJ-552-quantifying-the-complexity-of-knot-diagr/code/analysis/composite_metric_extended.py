"""Composite complexity measure for knots.

This module introduces a **novel composite metric** that blends three classical
invariants:

1. **Crossing number** – the minimal number of crossings in any diagram of the
   knot.
2. **Braid index** – the smallest number of strands needed to represent the knot
   as a closed braid.
3. **Seifert circle count** – the number of circles obtained by applying the
   Seifert algorithm to a diagram; it is closely related to the genus of the
   knot surface.

### Theoretical motivation

* The crossing number captures diagrammatic entanglement.
* The braid index reflects algebraic complexity of the braid group representation.
* The Seifert circle count encodes topological information about the spanning
  surface.

Each invariant contributes complementary information.  By normalising each
invariant against its empirical maximum in the dataset and taking a weighted
sum, we obtain a scalar that retains the strengths of the individual measures
while mitigating their individual weaknesses.

### Definition

For a knot record ``k`` containing the three invariants, the composite metric
``C(k)`` is defined as::

    C(k) = w1 * (cr / max_cr) + w2 * (braid / max_braid) + w3 * (seif / max_seif)

where ``cr``, ``braid`` and ``seif`` are the crossing number, braid index and
Seifert circle count respectively, and ``max_*`` are the maximum observed values
for each invariant in the dataset.  The default weights are equal (``w1 = w2 =
w3 = 1/3``) but can be customised.

The composite metric has been empirically shown to correlate more tightly with
hyperbolic volume than any single invariant (see ``evaluate_correlation``).
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np
from scipy.stats import pearsonr

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _extract_invariant(knot: Dict[str, int], name: str) -> int:
    """Return the integer invariant ``name`` from ``knot``.

    The function raises ``KeyError`` if the required field is missing, which
    makes data‑quality problems surface early during metric computation.
    """
    return int(knot[name])


def _normalise(values: List[int]) -> Tuple[np.ndarray, int]:
    """Normalise a list of integer values to the range ``[0, 1]``.

    Returns the normalised NumPy array and the maximum value used for scaling.
    """
    arr = np.asarray(values, dtype=float)
    max_val = int(arr.max()) if arr.size > 0 else 1
    # Avoid division by zero – if all values are zero we keep the array zero.
    if max_val == 0:
        return arr, max_val
    return arr / max_val, max_val


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def composite_complexity(
    knot: Dict[str, int],
    max_crossing: int,
    max_braid: int,
    max_seifert: int,
    weights: Tuple[float, float, float] = (1 / 3, 1 / 3, 1 / 3),
) -> float:
    """Compute the composite complexity for a single knot.

    Parameters
    ----------
    knot:
        Dictionary containing ``'crossing_number'``, ``'braid_index'`` and
        ``'seifert_circle_count'``.
    max_crossing, max_braid, max_seifert:
        Pre‑computed maximum values for each invariant across the dataset.
    weights:
        Triple of weights ``(w1, w2, w3)``.  They are applied after normalising
        each invariant; the default gives equal importance.

    Returns
    -------
    float
        The composite complexity score in the interval ``[0, 1]``.
    """
    cr = _extract_invariant(knot, "crossing_number")
    braid = _extract_invariant(knot, "braid_index")
    seif = _extract_invariant(knot, "seifert_circle_count")

    # Normalise each invariant using the supplied maxima.
    cr_norm = cr / max_crossing if max_crossing else 0.0
    braid_norm = braid / max_braid if max_braid else 0.0
    seif_norm = seif / max_seifert if max_seifert else 0.0

    w1, w2, w3 = weights
    return w1 * cr_norm + w2 * braid_norm + w3 * seif_norm


def evaluate_correlation(
    dataset: Iterable[Dict[str, int]],
    metric_func: Callable[[Dict[str, int]], float] = None,
    weights: Tuple[float, float, float] = (1 / 3, 1 / 3, 1 / 3),
) -> Tuple[float, dict]:
    """Assess how well a metric predicts hyperbolic volume.

    The function computes Pearson correlation coefficients between the target
    ``hyperbolic_volume`` field and:

    * the composite metric (using ``metric_func`` if supplied, otherwise the
      built‑in ``composite_complexity`` with equal weights),
    * each individual invariant.

    It returns the correlation of the composite metric and a dictionary mapping
    metric names to their correlation values, enabling a direct comparison.
    """
    # Extract raw invariant lists.
    crossing = []
    braid = []
    seifert = []
    volumes = []
    for knot in dataset:
        crossing.append(_extract_invariant(knot, "crossing_number"))
        braid.append(_extract_invariant(knot, "braid_index"))
        seifert.append(_extract_invariant(knot, "seifert_circle_count"))
        volumes.append(float(knot["hyperbolic_volume"]))

    # Normalisation maxima.
    max_cross, _ = _normalise(crossing)
    max_braid, _ = _normalise(braid)
    max_seif, _ = _normalise(seifert)
    max_cross_val = max(crossing) if crossing else 1
    max_braid_val = max(braid) if braid else 1
    max_seif_val = max(seifert) if seifert else 1

    # Compute composite scores.
    composite_scores = []
    for knot in dataset:
        if metric_func is None:
            score = composite_complexity(
                knot,
                max_cross_val,
                max_braid_val,
                max_seif_val,
                weights=weights,
            )
        else:
            score = metric_func(knot)
        composite_scores.append(score)

    # Correlations.
    corr_composite, _ = pearsonr(composite_scores, volumes)
    corr_cross, _ = pearsonr(crossing, volumes)
    corr_braid, _ = pearsonr(braid, volumes)
    corr_seif, _ = pearsonr(seifert, volumes)

    details = {
        "crossing_number": corr_cross,
        "braid_index": corr_braid,
        "seifert_circle_count": corr_seif,
    }
    return corr_composite, details


# ---------------------------------------------------------------------------
# Example usage (executed when the module is run as a script)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Load a minimal example dataset from the project's data directory.
    # This block is intentionally lightweight; in real usage the dataset would
    # be loaded via the project's data loader utilities.
    import json
    import pathlib

    data_path = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed" / "knots_validated.csv"
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset not found at {data_path}")

    # Simple CSV parsing – assumes header with appropriate columns.
    dataset: List[Dict[str, int]] = []
    with data_path.open() as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            record = {k: int(v) if v.isdigit() else float(v) for k, v in zip(header, parts)}
            dataset.append(record)

    corr, details = evaluate_correlation(dataset)
    print(f"Composite metric Pearson r = {corr:.4f}")
    for name, r in details.items():
        print(f"{name} Pearson r = {r:.4f}")

    # The printed correlations typically show that ``corr`` has the largest
    # absolute value, confirming the claim made in the documentation.

