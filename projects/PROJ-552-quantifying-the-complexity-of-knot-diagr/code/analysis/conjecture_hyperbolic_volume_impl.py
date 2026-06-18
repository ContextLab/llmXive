"""conjecture_hyperbolic_volume_impl.py
=======================================

This module implements the **Conjecture** linking the newly introduced
``CompositeMetric`` (see :pymod:`code.analysis.composite_metric_novel`) to the
hyperbolic volume of a knot complement.  The conjecture is inspired by
Thurston's theorem that the hyperbolic volume of a knot complement is bounded
above by a linear function of the crossing number.  Empirically we observe a
similar linear relationship when the *CompositeMetric* is used as the
independent variable.

The conjecture is stated as follows:

    **Conjecture 1 (Composite‑Metric Volume Bound).**  For any hyperbolic knot
    \(K\) in the census, let ``M(K)`` denote the value of the CompositeMetric
    defined in :pymod:`code.analysis.composite_metric_novel` and let
    ``Vol(K)`` be the hyperbolic volume of the knot complement.  Then there exist
    constants ``a > 0`` and ``b >= 0`` such that

    ``Vol(K) <= a * M(K) + b``.

The implementation below computes the best‑fit linear regression ``Vol = a * M
+ b`` across the full Knot Atlas census, stores the regression coefficients in a
JSON file, and generates a scatter plot with the regression line.  The results
are written to the ``data/processed`` directory so that downstream pipeline
stages (e.g., regression tables and visualization scripts) can consume them.

Usage
-----
The module can be invoked as a script or imported as a library.  When executed
directly it loads the processed knot data, evaluates the conjecture, and writes
the artefacts:

```bash
python -m code.analysis.conjecture_hyperbolic_volume_impl
```

The generated artefacts are:

* ``data/processed/conjecture_hyperbolic_volume_results.json`` – regression
  coefficients and R² statistic.
* ``data/plots/conjecture_hyperbolic_volume.png`` – scatter plot with regression
  line.

These files are referenced in the reproducibility documentation
(``docs/reproducibility/conjecture_hyperbolic_volume.md``) and are included in
the regression tables produced by :pymod:`code.analysis.regression`.
"""

from __future__ import annotations

import json
import pathlib
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load_processed_data() -> pd.DataFrame:
    """Load the processed knot dataset.

    The dataset ``data/processed/knots_validated.csv`` contains, among other
    columns, ``composite_metric_novel`` (the metric value) and ``hyperbolic_volume``.
    Only rows with non‑null values for both columns are retained.
    """
    csv_path = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed" / "knots_validated.csv"
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["composite_metric_novel", "hyperbolic_volume"])
    return df


def evaluate_conjecture(metric: List[float], volume: List[float]) -> Tuple[float, float, float]:
    """Perform linear regression ``volume = a * metric + b``.

    Returns
    -------
    a : float
        Slope of the regression line.
    b : float
        Intercept of the regression line.
    r_squared : float
        Coefficient of determination indicating goodness of fit.
    """
    slope, intercept, r_value, _, _ = stats.linregress(metric, volume)
    return slope, intercept, r_value ** 2


def _save_results(slope: float, intercept: float, r_squared: float) -> None:
    """Write regression results to JSON for downstream consumption."""
    results = {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "description": "Linear fit of hyperbolic volume vs. CompositeMetric (novel).",
    }
    out_path = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed" / "conjecture_hyperbolic_volume_results.json"
    out_path.write_text(json.dumps(results, indent=2))


def _plot(metric: List[float], volume: List[float], slope: float, intercept: float) -> None:
    """Create a scatter plot with the regression line and save it as PNG."""
    plt.figure(figsize=(8, 6))
    plt.scatter(metric, volume, alpha=0.6, edgecolor="k", label="Knot data")
    x_vals = np.array([min(metric), max(metric)])
    y_vals = slope * x_vals + intercept
    plt.plot(x_vals, y_vals, color="red", linewidth=2, label=f"Fit: y = {slope:.3f}x + {intercept:.3f}")
    plt.xlabel("CompositeMetric (novel)")
    plt.ylabel("Hyperbolic Volume")
    plt.title("Conjecture: CompositeMetric bounds Hyperbolic Volume")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    out_png = pathlib.Path(__file__).resolve().parents[3] / "data" / "plots" / "conjecture_hyperbolic_volume.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def run_conjecture_pipeline() -> None:
    """Execute the full conjecture evaluation pipeline.

    This function is the entry point used by the project’s main pipeline (see
    ``code/__init__.py``).  It loads data, evaluates the conjecture, stores the
    regression coefficients, and produces a plot.
    """
    df = _load_processed_data()
    metric_vals = df["composite_metric_novel"].tolist()
    volume_vals = df["hyperbolic_volume"].tolist()
    slope, intercept, r2 = evaluate_conjecture(metric_vals, volume_vals)
    _save_results(slope, intercept, r2)
    _plot(metric_vals, volume_vals, slope, intercept)


if __name__ == "__main__":
    run_conjecture_pipeline()


