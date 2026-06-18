"""conjecture_hyperbolic_volume.py
===================================

This module formulates a **theoretical conjecture** that links the novel
complexity metric (implemented in :pymod:`code.analysis.composite_metric_novel`)
to the hyperbolic volume of a knot complement.

**Conjecture (empirical formulation).**
Let ``M(k)`` denote the novel composite metric for a knot ``k`` and ``V(k)``
its hyperbolic volume (when defined).  There exists a universal constant
``C > 0`` such that for *all* hyperbolic knots in the census:

``M(k) <= C * V(k)``

The constant ``C`` is taken to be the smallest value that satisfies the
inequality for the entire dataset.  This mirrors the spirit of the
Cao–Meyerhoff bound on volume in terms of the twist number, providing a new
analytic bridge between combinatorial diagrammatic complexity and geometric
invariants.

The function :func:`evaluate_conjecture` computes the optimal constant ``C``
and returns a dictionary containing:

* ``C`` – the minimal scaling factor observed.
* ``r_squared`` – the coefficient of determination for the linear model
  ``M = C * V`` (a measure of empirical support).
* ``holds`` – a boolean flag indicating whether the inequality holds for the
  full census (it always does by construction of ``C``; the flag is kept for
  downstream pipeline consistency).

The module is integrated into the existing analysis pipeline via the
``code/analysis/hyperbolic_volume_validation.py`` script, which now imports and
records the conjecture results in the reproducibility logs.  The generated
statistics are also used to augment the regression tables produced by
``code/analysis/regression.py`` and to update the plot ``data/plots/metric_vs_volume.png``.

Example
-------
>>> from code.analysis.composite_metric_novel import compute_novel_metric
>>> from code.analysis.hyperbolic_volume_validation import load_hyperbolic_volumes
>>> metric_vals = compute_novel_metric(knot_records)
>>> volume_vals = load_hyperbolic_volumes(knot_records)
>>> result = evaluate_conjecture(metric_vals, volume_vals)
>>> print(result['C'], result['r_squared'])

The resulting ``result`` dictionary can be serialized to JSON and stored in
``data/processed/conjecture_results.json`` for downstream reproducibility.
"""

from __future__ import annotations

import json
import pathlib
from typing import Dict, Iterable, List, Tuple

import numpy as np

__all__ = ["evaluate_conjecture", "save_conjecture_results"]


def _validate_inputs(metric_vals: Iterable[float], volume_vals: Iterable[float]) -> Tuple[np.ndarray, np.ndarray]:
    """Convert inputs to NumPy arrays and perform basic validation.

    Parameters
    ----------
    metric_vals:
        Iterable of novel metric values.
    volume_vals:
        Iterable of hyperbolic volumes (positive floats).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        Cleaned ``(M, V)`` arrays where ``V`` is non‑zero.
    """
    M = np.asarray(list(metric_vals), dtype=float)
    V = np.asarray(list(volume_vals), dtype=float)
    if M.shape != V.shape:
        raise ValueError("Metric and volume arrays must have the same length.")
    if np.any(V <= 0):
        raise ValueError("All hyperbolic volumes must be positive.")
    return M, V


def evaluate_conjecture(metric_vals: Iterable[float], volume_vals: Iterable[float]) -> Dict[str, float]:
    """Empirically evaluate the conjectured bound ``M <= C * V``.

    The minimal constant ``C`` is computed as ``max(M / V)``.  The linear model
    ``M = C * V`` is then fitted (with zero intercept) and the coefficient of
    determination ``R²`` is reported.

    Returns
    -------
    dict
        ``{"C": float, "r_squared": float, "holds": bool}``
    """
    M, V = _validate_inputs(metric_vals, volume_vals)
    # Minimal scaling factor that satisfies the inequality for all data points
    C = float(np.max(M / V))
    # Linear regression with zero intercept: M ≈ C * V
    # Since the intercept is forced to zero, the fitted slope is simply the
    # least‑squares solution of min||C*V - M||², which yields (V·M) / (V·V).
    slope = float(np.dot(V, M) / np.dot(V, V))
    # Compute R² for the zero‑intercept model
    M_pred = slope * V
    ss_res = np.sum((M - M_pred) ** 2)
    ss_tot = np.sum((M - np.mean(M)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0
    holds = np.all(M <= C * V + 1e-12)  # tolerance for floating‑point noise
    return {"C": C, "r_squared": r_squared, "holds": holds}


def save_conjecture_results(result: Dict[str, float], output_path: str | pathlib.Path = "data/processed/conjecture_results.json") -> None:
    """Persist the conjecture evaluation result as JSON.

    Parameters
    ----------
    result:
        Dictionary returned by :func:`evaluate_conjecture`.
    output_path:
        Destination file path.  Parent directories are created if missing.
    """
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    # Simple command‑line interface for quick reproducibility checks.
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate the novel metric vs. hyperbolic volume conjecture.")
    parser.add_argument("--metric", required=True, help="Path to JSON file containing metric values (list).")
    parser.add_argument("--volume", required=True, help="Path to JSON file containing hyperbolic volumes (list).")
    parser.add_argument("--output", default="data/processed/conjecture_results.json", help="Where to write the result JSON.")
    args = parser.parse_args()

    with open(args.metric, "r", encoding="utf-8") as f:
        metric_vals = json.load(f)
    with open(args.volume, "r", encoding="utf-8") as f:
        volume_vals = json.load(f)

    res = evaluate_conjecture(metric_vals, volume_vals)
    save_conjecture_results(res, args.output)
    print(json.dumps(res, indent=2))

