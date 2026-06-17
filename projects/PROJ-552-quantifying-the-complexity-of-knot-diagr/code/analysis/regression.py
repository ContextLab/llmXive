"""
Regression analysis utilities.

The original implementation raised a ``ValueError`` when either the alternating
or non‑alternating group was empty.  This caused the end‑to‑end pipeline to
abort on datasets where one class is absent (e.g. after filtering).  The
function ``compute_descriptive_comparison`` now handles empty groups gracefully
by returning ``None`` for the missing statistics instead of raising.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np

# ----------------------------------------------------------------------
# Helper functions (unchanged)
# ----------------------------------------------------------------------


def fit_linear(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Fit a simple linear model."""
    coeffs = np.polyfit(x, y, 1)
    return {"slope": coeffs[0], "intercept": coeffs[1]}


def fit_polynomial(x: np.ndarray, y: np.ndarray, degree: int = 2) -> Dict[str, Any]:
    """Fit a polynomial model of the given degree."""
    coeffs = np.polyfit(x, y, degree)
    return {"coeffs": coeffs.tolist()}


def fit_logarithmic(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Fit a model of the form y = a * log(b * x + c) + d."""
    # Simple linear fit on log‑transformed x as a placeholder.
    log_x = np.log(x + 1e-8)
    coeffs = np.polyfit(log_x, y, 1)
    return {"a": coeffs[0], "b": 1.0, "c": 0.0, "d": coeffs[1]}


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def compute_descriptive_comparison(
    df: Any,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Compute descriptive statistics for alternating vs non‑alternating knots.

    Returns a tuple ``(alternating_stats, non_alternating_stats)`` where each
    element is either a dictionary of statistics or ``None`` if the group is
    empty.  This prevents the pipeline from crashing when a filter removes all
    members of one class.
    """
    # Split the dataframe.
    alt = df[df["alternating"] == True]  # noqa: E712
    non_alt = df[df["alternating"] == False]  # noqa: E712

    def _stats(group: Any) -> Optional[Dict[str, Any]]:
        if len(group) == 0:
            return None
        return {
            "count": int(group.shape[0]),
            "mean_crossing": float(group["crossing_number"].mean()),
            "mean_braid": float(group["braid_index"].mean()),
            "std_crossing": float(group["crossing_number"].std()),
            "std_braid": float(group["braid_index"].std()),
        }

    return _stats(alt), _stats(non_alt)


def run_regression_analysis(df: Any, output_path: Path) -> None:
    """
    Run the full regression workflow and write a JSON report to ``output_path``.
    """
    # Fit models.
    x = df["crossing_number"].to_numpy()
    y = df["volume"].to_numpy()

    results = {
        "linear": fit_linear(x, y),
        "polynomial": fit_polynomial(x, y),
        "logarithmic": fit_logarithmic(x, y),
    }

    # Add descriptive comparison (may contain ``None`` entries).
    alt_stats, non_alt_stats = compute_descriptive_comparison(df)
    results["descriptive_comparison"] = {
        "alternating": alt_stats,
        "non_alternating": non_alt_stats,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def main() -> None:  # pragma: no cover
    """
    Entry‑point used by the quickstart script.
    """
    from analysis.data_quantities import load_cleaned_knots_data

    df = load_cleaned_knots_data()
    out = Path("data/analysis/regression_report.json")
    run_regression_analysis(df, out)
